from common import *

json_string = """
{
  "blockchain":
  {
    "Contract A 0":
    {
      "address": "ox123",

      "userBalances":
      {
        "oy123": 100,
        "oz123": 200
      },
      "balance": 10000
    },
    "Contract B 1":
    {
      "address": "oy123",
      "balance": 200
    },
    "Contract B 2":
    {
      "address": "oz123",
      "balance": 300
    }
  },

  "transactions":
  {
    "transaction (1)":
    {
      "code": "ox123.trigger()"
    }
  }

}"""

import json
data = json.loads(json_string)
contracts=[]
Blockchain=""
maps=[("userBalances", "address", "uint")]
statics=""
for contract in data["blockchain"]:
  line=contract.split()
  name=line[1]+line[2]
  statics=statics+"public static " + line[1] +  " " + name + " = new " + line[1] + "();\n"
  i=0
  s=""
  for e in data["blockchain"][contract]:
    if e=="address":
      s=s+name+".address=" + "\"" + data["blockchain"][contract][e] + "\";\n"
      s=s+"addresses[" + str(i) + "]=" + name + ";\n"
      i=i+1
    elif e=="balance":
      s=s+name+".balance=" + str(data["blockchain"][contract][e]) + ";\n"
    elif map_tuple_contains(maps, e):
      tup=find_tuple_in_map(maps, e)
      j=0
      array_name=tup[0]+tup[1]
      for x in data["blockchain"][contract][e]:
        if not tup[2]=="String":
          s = s + name + "." + e + "[" + str(j) + "]=" + str(data["blockchain"][contract][e][x]) + ";\n"
        else:
          s = s + name + "." + e + "[" + str(j) + "]=\"" + str(data["blockchain"][contract][e][x]) + "\";\n"
        s=s+array_name+"[" + str(j) + "]=" + find_contract_by_address(data, x) + ";\n"
        j=j+1
  contracts.append(s)

# to print out Env
print "class Env {"
print statics
print "public static void init() { "
for c in contracts:
  print c
print "}"
print "}"
