import os, ctypes
from random import choice as rchoice
from getpass import getpass
from datetime import datetime, timedelta
from hashlib import md5, sha256
from timeit import default_timer as timer

ploc = os.path.expanduser('~') + os.sep + '.diary'              # Config location
rustLib = "target/release/libanecdote.so"                       # Library location

def hexed(text):                                                # Hexing function
    return map(lambda i:
        format(ord(i), '02x'), list(text))

def hashed(hashFunction, text):                                 # Hashing function (could be MD5 or SHA-256)
    hashObject = hashFunction()
    hashObject.update(text)
    return hashObject.hexdigest()

def char(text):                                                 # Hex-decoding function
    split = [text[i:i+2] for i in range(0, len(text), 2)]
    try:
        return ''.join(i.decode('hex') for i in split)
    except TypeError:
        return None

# use a random seed and CBC here...

def CXOR(text, key):                                            # Byte-wise XOR
    def xor(char1, char2):
        return chr(ord(char1) ^ ord(char2))
    out = ''
    i, j = 0, 0
    while i < len(text):
        out += xor(text[i], key[j])
        (i, j) = (i + 1, j + 1)
        if j == len(key):
            j = 0
    return ''.join(out)

def shift(text, amount):                                        # Shifts the ASCII value of the chars
    try:
        shiftedText = ''
        for i, ch in enumerate(text):
            shiftChar = (ord(ch) + amount) % 256
            shiftedText += chr(shiftChar)
    except TypeError:
        return None
    return shiftedText

def zombify(mode, data, key):                                   # Linking helper function
    hexedKey = ''.join(hexed(key))
    ch = sum([ord(i) for i in hexedKey])
    if mode == 'e':
        text = ''.join(hexed(data))
        return CXOR(shift(text, ch), key)
    elif mode in ('d', 'w'):
        text = shift(CXOR(data, key), 256 - ch)
        return char(text)

def temp(fileTuple, key):                                       # Decrypts and prints the story on the screen
    if type(fileTuple) == tuple:
        if protect(fileTuple[0], 'd', key):
            print 'Your story from', fileTuple[1], '...'
            with open(loc + 'TEMP.tmp', 'r') as file:
                data = file.readlines()
            print "\n<----- START OF STORY ----->\n"
            print ''.join(data)
            print "<----- END OF STORY ----->"
            os.remove(loc + 'TEMP.tmp')
            return key
        else:
            return None
    elif type(fileTuple) == str:
        return key
    else:
        return None

def check():                                                    # Allows password to be stored locally
    if not os.path.exists(ploc):
        try:
            while True:
                key = getpass('\nEnter your password: ')
                if len(key) < 8:
                    print 'Choose a strong password! (at least 8 chars)'
                    continue
                if getpass('Re-enter the password: ') == key:
                    break
                else:
                    print "\nPasswords don't match!"
            hashedKey = hashed(sha256, key)
            with open(ploc, 'w') as file:
                file.writelines([hashedKey + '\n'])
            print '\nLogin credentials have been saved locally!'
        except KeyboardInterrupt:
            print "\nInterrupted! Couldn't store login credentials!"
            return True
    else:
        try:
            with open(ploc, 'r') as file:
                hashedKey = file.readlines()[0][:-1]
            key = getpass('\nEnter your password to continue: ')
            if not hashedKey == hashed(sha256, key):
                # Fails if the password doesn't match with the credentials
                print 'Wrong password!'
                return None
        except KeyboardInterrupt:
            print 'Failed to authenticate!'
            return True
    return key

def protect(path, mode, key):                                   # A simple method which shifts and turns it to hex!
    with open(path, 'r') as file:
        data = file.readlines()
    if not len(data):
        print 'Nothing in file!'
        return key
    data = zombify(mode, ''.join(data), key)
    if not data:
        # Couldn't extract the chars from bytes! Indicates failure while decrypting
        print '\n\tWrong password!'
        return None
    File = (path if mode in ('e', 'w') else (loc + 'TEMP.tmp') if mode == 'd' else None)
    with open(File, 'w') as file:
        file.writelines([data])
    return key

def write(key, fileTuple = None):                               # Does the dirty writing job
    if not fileTuple:
        now = datetime.now()
        date = hashed(md5, 'Day ' + now.strftime('%d') + ' (' + now.strftime('%B') + ' ' + now.strftime('%Y') + ')')
        story = '\nYour story from {date:%B} {date:%d}, {date:%Y} ({date:%A}) ...'.format(date = now)
        fileTuple = (loc + date, story)
    elif type(fileTuple) == str:
        return key
    File = fileTuple[0]
    if os.path.exists(File) and os.path.getsize(File):
        # Intentionally decrypting the original file
        key = protect(File, 'w', key)
        # It's an easy workaround to modify your original story
        if not key:
            return None
        else:
            print '\nFile already exists! Appending to current file...'
    timestamp = str(datetime.now()).split('.')[0].split(' ')
    data = ['[' + timestamp[0] + '] ' + timestamp[1] + '\n']
    try:
        stuff = raw_input("\nStart writing... (Press Ctrl+C when you're done!)\n\n\t")
        data.append(stuff)
    except KeyboardInterrupt:
        print '\nNothing written! Quitting...'
        if os.path.exists(File) and os.path.getsize(File):
            key = protect(File, 'e', key)
        return key
    while True:
        try:
            stuff = raw_input('\t')
            # Auto-tabbing of paragraphs (for each <RETURN>)
            data.append(stuff)
        except KeyboardInterrupt:
            break
    with open(File, 'a') as file:
        file.writelines('\n\t'.join(data) + '\n\n')
    key = protect(File, 'e', key)
    ch = raw_input('\nSuccessfully written to file! Do you wanna see it (y/n)? ')
    if ch == 'y':
        temp(fileTuple, key)
    return key

def hashDate(year = None, month = None, day = None):            # Return a path based on (day, month, year) input
    while True:
        try:
            if not year:
                year = raw_input('\nYear: ')
            if not month:
                month = raw_input('\nMonth: ')
            if not day:
                day = raw_input('\nDay: ')
            date = datetime(int(year), int(month), int(day))
            if date:
                year = date.strftime('%Y')
                month = date.strftime('%B')
                day = date.strftime('%d')
                break
        except Exception as err:
            print "An error occurred:", err
            year, month, day = None, None, None
            continue
    fileName = loc + hashed(md5, 'Day ' + day + ' (' + month + ' ' + year + ')')
    if not os.path.exists(fileName):
        if date > datetime.now():
            print 'You cannot write/view a story for a day in the future!'
            return 'blah'
        print '\nNo stories on {date:%B} {date:%d}, {date:%Y} ({date:%A}).'.format(date = date)
        return None
    story = '{date:%B} {date:%d}, {date:%Y} ({date:%A})'.format(date = date)
    # This will be useful for displaying the date of story
    return fileName, story

def findStory(delta, date = datetime(2014, 12, 13)):            # Finds the file name using the timedelta from the birth of the diary to a specified date
    stories = len(os.listdir(loc))
    d = date + timedelta(days = delta)
    fileName = hashDate(d.year, d.month, d.day)
    if not fileName:
        return None
    return fileName

def random(key):                                                # Useful only when you have a lot of stories (obviously)
    stories = len(os.listdir(loc))
    while True:
        ch = rchoice(range(stories))
        fileName = findStory(ch)
        if fileName:
            break
    return temp(fileName, key)

def configure(delete = False):                                  # Configuration file for authentication
    try:
        choice = 'y'
        if os.path.exists(ploc) and not delete:
            print 'Configuration file found!'
            with open(ploc, 'r') as file:
                config = file.readlines()
            if len(config) > 1:
                loc = config[1]
                key = check()
                if type(key) is not str:
                    return None, None, 'n'
            else:
                delete = True
        if delete:
            print 'Deleting configuration file...'
            os.remove(ploc)
        if not os.path.exists(ploc):
            print "\nLet's start configuring your diary..."
            loc = raw_input('Enter the (absolute) location for your diary: ')
            while not os.path.exists(loc):
                print 'No such path exists!'
                loc = raw_input('Please enter a valid path: ')
            if loc[-1] is not os.sep:
                loc += os.sep
            key = check()
            if type(key) is not str:
                return None, None, 'n'
            with open(ploc, 'a') as file:
                file.writelines([loc])                          # Store the location along with the password hash
    except KeyboardInterrupt:
        return None, None, 'n'
    return loc, key, choice

def grabStories(delta, date):                                   # Grabs the story paths for a given datetime and timedelta objects
    fileData = [], []
    for i in range(delta):
        fileName = findStory(i, date)
        if fileName == None:
            continue
        fileData[0].append(fileName[0])
        fileData[1].append(fileName[1])
    return fileData

def pySearch(key, files, word):                                 # Exhaustive process might do better with a low-level language
    occurrences = []                                            # That's why I'm writing a Rust library for this...
    displayProg = 0
    printed = False
    total = len(files)
    start = timer()
    for i, File in enumerate(files):
        progress = int((float(i + 1) / total) * 100)
        if progress is not displayProg:
            displayProg = progress
            printed = False
        occurred = 0
        if protect(File, 'd', key):
            with open(loc + 'TEMP.tmp', 'r') as file:
                data = file.readlines()
            occurred = ''.join(data).count(word)
        else:
            print 'Cannot decrypt story! Skipping... (filename hash: %s)' % File.split(os.sep)[-1]
        occurrences.append(occurred)
        if not printed:
            print 'Progress: %d%s \t(Found: %d)' % (displayProg, '%', sum(occurrences))
            printed = True
    stop = timer()
    return occurrences, (stop - start)

def rustySearch(key, pathList, word):                           # Give the searching job to Rust!
    lib = ctypes.cdll.LoadLibrary(rustLib)
    list_to_send = pathList[:]
    list_to_send.extend((key, word))
    # send an array pointer full of string pointers
    c_array = (ctypes.c_char_p * len(list_to_send))(*list_to_send)
    start = timer()
    lib.get_stuff(c_array, len(list_to_send))
    stop = timer()
    return (stop - start)

def search(key):
    word = raw_input("Enter a word: ")
    choice = int(raw_input("\n\t1. Search everything! (Python)\n\t2. Search between two dates\n\t3. Search everything! (Rust)\n\nChoice: "))
    if choice in (1, 3):
        d1 = datetime(2014, 12, 13)
        d2 = datetime.now()
    while choice == 2:
        try:
            print '\nEnter dates in the form YYYY-MM-DD (Mind you, with hyphen!)'
            d1 = datetime.strptime(raw_input('Start date: '), '%Y-%m-%d')
            d2 = raw_input("End date (Press <Enter> for today's date): ")
            if not d2:
                d2 = datetime.now()
            else:
                d2 = datetime.strptime(d2, '%Y-%m-%d')
        except ValueError:
            print '\nOops! Error in input. Try again...'
            continue
        break
    delta = (d2 - d1).days
    print '\nDecrypting %d stories...\n' % delta
    files = grabStories(delta, d1)
    # has both file location and the formatted datetime
    if choice in (1, 2):
        fileData, timing = pySearch(key, files[0], word)
    else:
        rustySearch(key, files[0], word)
        return key
    print "\nSearch results from {d1:%B} {d1:%d}, {d1:%Y} to {d2:%B} {d2:%d}, {d2:%Y}.".format(d1 = d1, d2 = d2)
    if sum(fileData):
        print "\nStories on these days have the word '%s' in them...\n" % word
    else:
        print '\nTime taken:', timing, 'seconds!'
        print '\nBummer! Nothing...'
        return key
    # splitting into pairs
    results = [(files[0][i], files[1][i]) for i, count in enumerate(fileData) if count]
    for i, data in enumerate(results):
        print str(i + 1) + '. ' + data[1]               # print only the datetime
    print '\nTime taken:', timing, 'seconds!'
    print '\nFound %d occurrences in %d stories!\n' % (sum(fileData), len(results))
    os.remove(loc + 'TEMP.tmp')
    while files:
        try:
            ch = int(raw_input('Enter the number to see the corresponding story: '))
            temp((results[ch-1][0], results[ch-1][1]), key)
        except Exception:
            print '\nOops! Bad input...\n'
    return key

if __name__ == '__main__':
   loc, key, choice = configure()
   while choice is 'y':
       if os.path.exists(loc + 'TEMP.tmp'):
           os.remove(loc + 'TEMP.tmp')
       try:
           print '\n### This program runs best on Linux terminal ###'
           while True:
               choices = ('\n\tWhat do you wanna do?\n',
                   " 1: Write today's story",
                   " 2: Random story",
                   " 3: View the story of someday",
                   " 4. Write the story for someday you've missed",
                   " 5. Search your stories",
                   " 6. Reconfigure your diary",)
               print '\n\t\t'.join(choices)
               try:
                   ch = int(raw_input('\nChoice: '))
                   if ch in range(1, 7):
                       break
                   else:
                       print '\n\tPlease enter a value between 0 and 6!'
               except ValueError:
                   print "\n\tC'mon, quit playing around and start writing..."
           options = ['write(key)', 'random(key)', 'temp(hashDate(), key)', 'write(key, hashDate())', 'search(key)', 'configure(True)']
           try:
               key = eval(options[int(ch)-1])                  # just to remember the password throughout the session
           except Exception as err:                            # But, you have to sign-in for each session!
               print "\nAh, something bad has happened! Did you do it?"
           choice = raw_input('\nDo something again (y/n)? ')
       except KeyboardInterrupt:
           choice = raw_input('\nInterrupted! Do something again (y/n)? ')
   if choice is not 'y':
       print '\nGoodbye...'
