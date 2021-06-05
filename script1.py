import sys

def hi(a):
  return 'Hi'+a

if __name__ == '__main__':
    #  print(globals()[sys.argv[2]](sys.argv[1]))
    print(hi(' '.join(sys.argv[1::])))