import glob 
import toml

vals = glob.glob("transactions/*-validator.toml")
count = 0

for v in vals:
    p = toml.load(open(v, "r"))
    if float(p['validator_account'][0]['commission_rate']) < 0.05:
        name = p['validator_account'][0]['metadata']['name']
        print(name, p['validator_account'][0]['commission_rate'])
        count += 1

print(count)
    