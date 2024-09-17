# License for original (reference) implementation:
#
# Copyright (c) 2017, 2020 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Reference implementation for Bech32/Bech32m and segwit addresses."""
"""This implementation removes the constrain of maximum 90 characters."""


from collections.abc import ByteString
from enum import Enum
from typing import NamedTuple


class Encoding(Enum):
    """Enumeration type to list the various supported encodings."""

    BECH32 = 1
    BECH32M = 2


CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32M_CONST = 0x2BC830A3


class DecodeError(ValueError):
    pass


class HrpDoesNotMatch(DecodeError):
    pass


class DecodedAddress(NamedTuple):
    witver: int
    witprog: bytes


def bech32_polymod(values: ByteString) -> int:
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp: str) -> bytes:
    """Expand the HRP into values for checksum computation."""
    return bytes([ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp])


def bech32_verify_checksum(hrp: str, data: bytes) -> Encoding:
    """Verify a checksum given HRP and converted data characters."""
    const = bech32_polymod(bech32_hrp_expand(hrp) + data)
    if const == 1:
        return Encoding.BECH32
    if const == BECH32M_CONST:
        return Encoding.BECH32M
    # Invalid checksum
    raise DecodeError()


def bech32_decode(bech: str) -> tuple[str, memoryview, Encoding]:
    """Validate a Bech32/Bech32m string, and determine HRP and data."""
    if (any(ord(x) < 33 or ord(x) > 126 for x in bech)) or (
        bech.lower() != bech and bech.upper() != bech
    ):
        # HRP character out of range
        raise DecodeError()
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech):
        # No separator character / Empty HRP / overall max length exceeded
        raise DecodeError()
    if not all(x in CHARSET for x in bech[pos + 1 :]):
        # Invalid data character
        raise DecodeError()
    hrp = bech[:pos]
    data = memoryview(bytes(CHARSET.find(x) for x in bech[pos + 1 :]))
    spec = bech32_verify_checksum(hrp, data)
    return (hrp, data[:-6], spec)


def convertbits(data: ByteString, frombits: int, tobits: int, pad: bool = True) -> bytearray:
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = bytearray()
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            # XXX Not covered by tests
            raise DecodeError()
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        # More than 4 padding bits / Non-zero padding in 8-to-5 conversion
        raise DecodeError()
    return ret


def decode(hrp: str, addr: str) -> DecodedAddress:
    """Decode a segwit address."""
    hrpgot, data, spec = bech32_decode(addr)
    if hrpgot != hrp:
        raise HrpDoesNotMatch()
    witprog = convertbits(data[1:], 5, 8, False)
    if len(witprog) < 2 or len(witprog) > 40:
        # Invalid program length
        raise DecodeError()
    witver = data[0]
    if witver > 16:
        # Invalid witness version
        raise DecodeError()
    if witver == 0 and len(witprog) != 20 and len(witprog) != 32:
        # Invalid program length for witness version 0 (per BIP141)
        raise DecodeError()
    if witver == 0 and spec != Encoding.BECH32 or witver != 0 and spec != Encoding.BECH32M:
        # Invalid checksum algorithm
        raise DecodeError()
    return DecodedAddress(witver, witprog)


def is_valid_bech32m(data, hrp):
    try:
        this_hrp, _, _ = bech32_decode(data)
        return this_hrp == hrp
    except Exception:
        return False
