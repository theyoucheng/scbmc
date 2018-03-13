import argparse
import re
import sys
import string
import os

def remove_comments(string):
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
    # first group captures quoted strings (double or single)
    # second group captures comments (//single-line or /* multi-line */)
    regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return "" # so we will return empty to remove the comment
        else: # otherwise, we will return the 1st group
            return match.group(1) # captured quoted-string
    return regex.sub(_replacer, string)


#def preprocess_input(fname):
#  #os.system("cp %s %s", fname, fname+"_")
#  shutil.copy2(fname, fname+"_")
#  with open(fname+"_", 'r+') as f:
#    lines = f.readlines()
#    f.seek(0)
#    f.truncate()
#    for line in lines:
#      line=remove_comments(line)
#      line = line.replace("{", "\n {")
#      line = line.replace(" returns ", "\n returns ")
#      line=lazy_replacement(line)
#      f.write(line)

def get_func_name(line):
  name=""
  nex=False
  for x in line:
    if nex and name!="" and (x=="" or x=="("):
      return name
    if x==" ":
      name=""
      continue
    name=name+x
    if name=="void":
      nex=True

def is_primitive(x):
  if x=="int" or x=="double" or x=="address" or x=="boolean" or x=="" or x=="String":
    return True
  #for s in struct_list:
  #  if x==s: return True
  #return False

def contains(S, s):
  pos=S.find(s)
  if pos<0: return False
  return True

def in_list(L, e):
  for x in L:
    if x==e: return True
  return False

def in_map(L, e):
  for x in L:
    if x[0]==e: return True
  return False

#def list_contains(l, e):
#  for x in l:
#    if x==e: return True
#  return False
#
def map_tuple_contains(l, e):
  for x in l:
    if e==x[0]: return True
  return False

def find_tuple_in_map(l, e):
  for x in l:
    if e==x[0]: return x

def find_contract_by_address(data, x):
  for contract in data["blockchain"]:
    if data["blockchain"][contract]["address"]==x:
      line=contract.split()
      return line[1]+line[2]

def keyword(line, x):
  return contains(line, x+" ") or contains(line, x)

def get_last_literal(line):
  line=line.replace("\n", "")
  literals=line.split(" ")
  return literals[len(literals)-1]

class Contract(object):
  def __init__(self):
    self.name=""
    self.dependency=[]
    self.mappings=[]
    self.body=""

  def copy(self):
    contract=Contract()
    contract.name=self.name
    contract.dependency=self.dependency
    contract.mappings=self.mappings
    contract.body=self.body
    return contract

  def clear(self):
    self.name=""
    self.dependency=[]
    self.mappings=[]
    self.body=""

def sort_contract_list(contracts):
  n=len(contracts)
  for i in range(0, n-1):
    for j in range(0, n-1):
      if in_list(contracts[j].dependency, contracts[j+1].name):
        temp=contracts[j]
        contracts[j]=contracts[j+1]
        contracts[j+1]=temp
  return contracts
