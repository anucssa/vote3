try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import hashlib
import subprocess
import sys

try:
    server = sys.argv[1]
except Exception:
    print("Usage: vat.py http://SERVER/vote/audit")
    print("       where SERVER is the server hosting the election")
    sys.exit(1)


# try to open a null to pipe GPG output to
# apparently nul works on windows:
# http://gcc.gnu.org/ml/gcc-patches/2005-05/msg01793.html
try:
    null = open('/dev/null', 'w')
except IOError:
    try:
        null = open('nul', 'w')
    except IOError:
        null = None
    
print("Checking GPG:")
has_gpg = (subprocess.call(['gpg', '--version'], stdout=null) == 0)
print("GPG is " + ("present" if has_gpg else "not present"))
print("")

print("Auditing " + server)

has_key=True
try:
    print("Downloading capstone entry.")
    e = urlopen(server + "/count/raw")
    d = e.readlines()
    d = [l.decode('UTF-8') for l in d]
except IOError:
    print("Failed. Is the server online?")
    sys.exit(2)

try:
    [count_str] = [x for x in d if len(x) > 1 and
                   all([c in '0123456789\n' for c in x])]
    count = int(count_str.strip())
    [finalhash] = [x for x in d if len(x) == 97 and
                  all([c in '0123456789abcdef\n' for c in x])]
    finalhash = finalhash.strip()
except:
    print("Couldn't find hash or count in capstone entry.")
    print("Please check /audit/count/")
    sys.exit(3)

# try verification
process = subprocess.Popen(['gpg'], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
(stdout, stderr) = process.communicate(''.join(d).encode('UTF-8'))
if process.returncode == 0:
    print("Signature verification succeeded.")
elif process.returncode == 2:
    print("Signature verification failed - probably missing key.")
    print("GPG standard error:")
    print(stderr.decode('UTF-8'))
    print("Assuming there's no key and carrying on.")
    has_key = False
else:
    print("Signature verification failed!")
    print("GPG standard output:")
    print(stdout.decode('UTF-8'))
    print("GPG standard error:")
    print(stderr.decode('UTF-8'))
    print("AUDIT VERIFICATION FAILED")
    sys.exit(2)

pasthash = ''
for entry in range(1, count+1):
    try:
        print("Downloading entry " + str(entry))
        e = urlopen(server + "/" + str(entry) + "/raw")
        d = e.readlines()
        d = [l.decode('UTF-8') for l in d]
    except IOError:
        print("Failed.")
        print("AUDIT TRAIL VERIFICATION FAILED")
        print("Failed to download entry: " + str(entry))
        sys.exit(2)

    # Hash Verification
    if entry == 1:
        print("This is the first entry, skipping hash verification.")
    else:
        try:
            [thishash] = [x for x in d if len(x) == 97 and
                          all([c in '0123456789abcdef\n' for c in x])]
            thishash = thishash.strip()
        except:
            print("No hash found!")
            print("The entry is:")
            print(''.join(d))
            print("AUDIT VERIFICATION FAILED")
            sys.exit(2)

        if thishash == pasthash:
            print("Hash verification succeded.")
        else:
            print("Hash mismatch!")
            print("Our hash of the previous message:")
            print(pasthash)
            print("Stated hash of the previous message:")
            print(thishash)
            print("The entry is:")
            print(''.join(d))
            print("AUDIT VERIFICATION FAILED")
            sys.exit(2)
    pasthash = hashlib.sha384(''.join(d).encode('UTF-8')).hexdigest()

    # Signature verification
    if has_gpg and has_key:
        process = subprocess.Popen(['gpg'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate(''.join(d).encode('UTF-8'))
        if process.returncode == 0:
            print("Signature verification succeeded.")
        else:
            print("Signature verification failed!")
            print("GPG standard output:")
            print(stdout.decode('UTF-8'))
            print("GPG standard error:")
            print(stderr.decode('UTF-8'))
            print("AUDIT VERIFICATION FAILED")
            sys.exit(2)

# verify final hash from capstone
if finalhash == pasthash:
    print("Capstone hash matches final hash.")
else:
    print("Hash mismatch!")
    print("Our hash of the final message:")
    print(pasthash)
    print("Stated hash of the final message (from the capstone message):")
    print(finalhash)
    print("AUDIT VERIFICATION FAILED")
    sys.exit(2)
    
if has_gpg and has_key:
    print("\nAUDIT VERIFICATION SUCCESSFUL")
    print(
"""Note: all that has been verfied is that the sequence of
messages has not been tampered with. You can manually verify that:

 * that the content of the messages is as expected (e.g. the election
   is not changed midway through)
 * the count is as expected
 * if you voted, that your vote is present
 
(Eventually there will be tools to do some of these, but they haven't been
written yet.)""")
else:
    print("\nAUDIT VERIFICATION PARTIALLY SUCCESSFUL")
    print(
"""The hash chain has been verfied, but the digital signatures have
not been verified. This provides causal verification against
programming errors, but not against deliberate tampering.

For more integrity, install GPG and the Vote3 signing key.""")
