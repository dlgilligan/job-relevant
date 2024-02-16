import sys
from BitVector import *

PassPhrase = "Hopes and dreams of a million years"
BLOCKSIZE = 16
numbytes = BLOCKSIZE // 8

# Reduce the passphrase to a bit array of size BLOCKSIZE
bv_iv = BitVector(bitlist = [0]*BLOCKSIZE)
for i in range(0,len(PassPhrase) // numbytes):
    textstr = PassPhrase[i*numbytes:(i+1)*numbytes]
    bv_iv ^= BitVector(textstring = textstr)

# Arguments:
# * ciphertextFile: String containing the file name of the ciphertext
# * key_bv : 16-bit BitVector for the decryption key
def cryptBreak(ciphertextFile, key_bv):
    # Create a bitvector from the ciphertext hex string
    FILEIN = open(ciphertextFile)
    encrypted_bv = BitVector( hexstring = FILEIN.read() )
    FILEIN.close()

    # Create a bitvector for storing the decrypted plaintext bit array
    msg_decrypted_bv = BitVector( size = 0 )

    # Carry out differential XORing of bit blocks and decryption
    previous_decrypted_block = bv_iv
    for i in range(0, len(encrypted_bv) // BLOCKSIZE):
        bv = encrypted_bv[i*BLOCKSIZE:(i+1)*BLOCKSIZE]
        temp = bv.deep_copy()
        bv ^= previous_decrypted_block
        previous_decrypted_block = temp
        bv ^= key_bv
        msg_decrypted_bv += bv

    # Extract plaintext from the decrypted bitvector:
    outputtext = msg_decrypted_bv.get_text_from_bitvector()

    # Return the output text
    return outputtext


if __name__ == "__main__":
    # Loop through 0 - ((2^16) - 1) keyspace
    # Call cryptBreak
    # If returned text contains ferrari, loop breaks
    # Do with key and output whatever is necessary
    # If returned text does not contain ferrari, increment bitvector and restart
    test_key = BitVector(bitlist = [0]*BLOCKSIZE)
    max_key = BitVector(bitlist = [1]*BLOCKSIZE)
    correct_key = 0

    while test_key <= max_key:
        decrypted_text = cryptBreak("cipherText.txt",test_key)

        if "Ferrari" in decrypted_text:
            correct_key = 1
            break

        test_key = BitVector(intVal = (test_key.int_val() + 1),size = BLOCKSIZE)

    if correct_key:
        print("Encryption Broken!")
        print("Encryption Key:")
        print(test_key)
        print("Decrypted Text:")
        print(decrypted_text)
    else:
        print("Error: Encryption not broken!")







