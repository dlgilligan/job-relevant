import sys
from BitVector import *

AES_modulus = BitVector(bitstring='100011011')
subBytesTable = []
invSubBytesTable = []

# Define the fixed matrix for MixColumns step
mix_columns_matrix = [
    [BitVector(intVal=2), BitVector(intVal=3), BitVector(intVal=1), BitVector(intVal=1)],
    [BitVector(intVal=1), BitVector(intVal=2), BitVector(intVal=3), BitVector(intVal=1)],
    [BitVector(intVal=1), BitVector(intVal=1), BitVector(intVal=2), BitVector(intVal=3)],
    [BitVector(intVal=3), BitVector(intVal=1), BitVector(intVal=1), BitVector(intVal=2)]
]

# Define the fixed matrix for InvMixColumns step
inv_mix_columns_matrix = [
    [BitVector(intVal=0x0E), BitVector(intVal=0x0B), BitVector(intVal=0x0D), BitVector(intVal=0x09)],
    [BitVector(intVal=0x09), BitVector(intVal=0x0E), BitVector(intVal=0x0B), BitVector(intVal=0x0D)],
    [BitVector(intVal=0x0D), BitVector(intVal=0x09), BitVector(intVal=0x0E), BitVector(intVal=0x0B)],
    [BitVector(intVal=0x0B), BitVector(intVal=0x0D), BitVector(intVal=0x09), BitVector(intVal=0x0E)]
]


def print_state_array(state_array, message):
    print("\n",message)
    for i in range(4):
        for j in range(4):
            temp = state_array[j][i]
            print(temp.get_hex_string_from_bitvector())
            
def genTables():
    c = BitVector(bitstring='01100011')
    d = BitVector(bitstring='00000101')
    for i in range(0, 256):
        # For the encryption SBox
        a = BitVector(intVal = i, size=8).gf_MI(AES_modulus, 8) if i != 0 else BitVector(intVal=0)
        # For bit scrambling for the encryption SBox entries:
        a1,a2,a3,a4 = [a.deep_copy() for x in range(4)]
        a ^= (a1 >> 4) ^ (a2 >> 5) ^ (a3 >> 6) ^ (a4 >> 7) ^ c
        subBytesTable.append(int(a))
        # For the decryption Sbox:
        b = BitVector(intVal = i, size=8)
        # For bit scrambling for the decryption SBox entries:
        b1,b2,b3 = [b.deep_copy() for x in range(3)]
        b = (b1 >> 2) ^ (b2 >> 5) ^ (b3 >> 7) ^ d
        check = b.gf_MI(AES_modulus, 8)
        b = check if isinstance(check, BitVector) else 0
        invSubBytesTable.append(int(b))

def ShiftRows(state_array):
    shifted_array = []
    for i in range(4):
        row = state_array[i]
        shifted_row = row[i:] + row[:i]
        shifted_array.append(shifted_row)

    return shifted_array

def InvShiftRows(state_array):
    shifted_array = []
    for i in range(4):
        row = state_array[i]
        shifted_row = row[-i:] + row[:-i]
        shifted_array.append(shifted_row)

    return shifted_array

def MixColumns(state_array):
    result = [[BitVector(intVal=0) for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] ^= mix_columns_matrix[i][k].gf_multiply_modular(state_array[k][j], BitVector(intVal=0x11B),8)
    return result

def InvMixColumns(state_array):
    result = [[BitVector(intVal=0) for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] ^= inv_mix_columns_matrix[i][k].gf_multiply_modular(state_array[k][j], BitVector(intVal=0x11B),8)
    return result

def SubBytes(state_array):
    subbed_array = []
    for i in range(4):
        subbed_row = []
        for j in range(4):
            curr = state_array[i][j]
            curr_int = convert(curr)

            result = subBytesTable[curr_int]
            subbed_row.append(BitVector(intVal=result, size=8))

        subbed_array.append(subbed_row)
    
    return subbed_array

def InvSubBytes(state_array):
    subbed_array = []
    for i in range(4):
        subbed_row = []
        for j in range(4):
            curr = state_array[i][j]
            curr_int = convert(curr)

            result = invSubBytesTable[curr_int]
            subbed_row.append(BitVector(intVal=result, size=8))

        subbed_array.append(subbed_row)
    
    return subbed_array

def convert(in_bv):
    return int(str(in_bv),2)

def gen_key_schedule_256(key_bv):
    byte_sub_table = gen_subbytes_table()
    # We need 60 keywords (each keyword consists of 32 bits) in the key schedule for
    # 256 bit AES. The 256-bit AES uses the first four keywords to xor the input
    # block with. Subsequently, each of the 14 rounds uses 4 keywords from the key
    # schedule. We will store all 60 keywords in the following list:
    key_words = [None for i in range(60)]
    round_constant = BitVector(intVal = 0x01, size=8)
    for i in range(8):
        key_words[i] = key_bv[i*32 : i*32 + 32]
    for i in range(8,60):
        if i%8 == 0:
            kwd, round_constant = gee(key_words[i-1], round_constant, byte_sub_table)
            key_words[i] = key_words[i-8] ^ kwd
        elif (i - (i//8)*8) < 4:
            key_words[i] = key_words[i-8] ^ key_words[i-1]
        elif (i - (i//8)*8) == 4:
            key_words[i] = BitVector(size = 0)
            for j in range(4):
                key_words[i] += BitVector(intVal = byte_sub_table[key_words[i-1][8*j:8*j+8].intValue()], size = 8)
            key_words[i] ^= key_words[i-8]
        elif ((i - (i//8)*8) > 4) and ((i - (i//8)*8) < 8):
            key_words[i] = key_words[i-8] ^ key_words[i-1]
        else:
            sys.exit("error in key scheduling algo for i = %d" % i)
    
    return key_words

def gen_subbytes_table():
    subBytesTable = []
    c = BitVector(bitstring='01100011')
    for i in range(0, 256):
        a = BitVector(intVal = i, size=8).gf_MI(AES_modulus, 8) if i != 0 else BitVector(intVal=0)
        a1,a2,a3,a4 = [a.deep_copy() for x in range(4)]
        a ^= (a1 >> 4) ^ (a2 >> 5) ^ (a3 >> 6) ^ (a4 >> 7) ^ c
        subBytesTable.append(int(a))
    return subBytesTable

def gee(keyword, round_constant, byte_sub_table):
    rotated_word = keyword.deep_copy()
    rotated_word << 8
    newword = BitVector(size = 0)
    
    for i in range(4):
        newword += BitVector(intVal = byte_sub_table[rotated_word[8*i:8*i+8].intValue()], size = 8)
    
    newword[:8] ^= round_constant
    round_constant = round_constant.gf_multiply_modular(BitVector(intVal = 0x02), AES_modulus, 8)
    
    return newword, round_constant

def create_state_array(plain_bv):
    state = [[0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            byte = plain_bv[i * 32 + j * 8: i * 32 + (j + 1) * 8]
            state[j][i] = byte
    
    return state

def add_round_key(state_array, key_array):
    for i in range(4):
        for j in range(4):
            state_array[i][j] ^= key_array[i][j]

    return state_array

class AES():
    def __init__(self, keyfile:str) -> None:
        genTables()

        with open(keyfile, 'r') as file:
            key_str = file.read().strip()
            key_bv = BitVector(textstring=key_str)

        self.key_schedule = gen_key_schedule_256(key_bv)

    def encrypt(self, plaintext:str, ciphertext:str) -> None:
        in_bv = BitVector(filename=plaintext)
        out_fp = open(ciphertext, 'w')

        while in_bv.more_to_read:
            temp = in_bv.read_bits_from_file(128)

            # Block Size Alignment
            if len(temp) < 128:
                temp += BitVector(size=128 - len(temp))

            # Create State Array
            state_array = create_state_array(temp)

            # XOR first four words of key schedule
            key_chunk = self.key_schedule[0] + self.key_schedule[1] + self.key_schedule[2] + self.key_schedule[3]
            key_array = create_state_array(key_chunk)
            state_array = add_round_key(state_array, key_array)

            # Perform rounds of encryption
            for i in range(1,14):
                # Substitute Bytes
                state_array = SubBytes(state_array)

                # Shift Rows
                state_array = ShiftRows(state_array)

                # Mix Columns
                state_array = MixColumns(state_array)

                # Add Key
                key_chunk = self.key_schedule[4*i] + self.key_schedule[(4*i) + 1] + self.key_schedule[(4*i) + 2] + self.key_schedule[(4*i) + 3]
                key_array = create_state_array(key_chunk)
                state_array = add_round_key(state_array, key_array)

            # Perform Final Round of encryption without MixColumns
            # Substitute Bytes
            state_array = SubBytes(state_array)

            # Shift Rows
            state_array = ShiftRows(state_array)

            # Add Key
            key_chunk = self.key_schedule[56] + self.key_schedule[57] + self.key_schedule[58] + self.key_schedule[59]
            key_array = create_state_array(key_chunk)
            state_array = add_round_key(state_array, key_array)

            ciphertext_hex = ''.join(['{:02x}'.format(state_array[i][j].intValue()) for j in range(4) for i in range(4)])
            out_fp.write(ciphertext_hex)
        
        out_fp.close()

    def decrypt(self, ciphertext:str, decrypted:str) -> None:
        decrypted_text = ""
        with open(ciphertext, 'r') as in_fp:
            while True:
                # Read 128 bits at a time
                ciphertext_hex = in_fp.read(32)  # 32 characters represent 128 bits in hex string
                if not ciphertext_hex:
                    break  # end of file
                ciphertext_bv = BitVector(hexstring=ciphertext_hex)

                # Convert hex string to state array
                state_array = create_state_array(ciphertext_bv)

                # XOR last four words of key schedule
                key_chunk = self.key_schedule[56] + self.key_schedule[57] + self.key_schedule[58] + self.key_schedule[59]
                key_array = create_state_array(key_chunk)
                state_array = add_round_key(state_array, key_array)

                # Perform rounds of decryption
                for i in range(13, 0, -1):  # Reverse order
                    # Inv Shift Rows
                    state_array = InvShiftRows(state_array)

                    # Inv Sub Bytes
                    state_array = InvSubBytes(state_array)

                    # XOR with Round Key
                    key_chunk = self.key_schedule[4 * i] + self.key_schedule[4 * i + 1] + self.key_schedule[4 * i + 2] + self.key_schedule[4 * i + 3]
                    key_array = create_state_array(key_chunk)
                    state_array = add_round_key(state_array, key_array)

                    # Inv Mix Columns
                    state_array = InvMixColumns(state_array)

                # Perform Final Round of decryption without InvMixColumns
                # Inv Shift Rows
                state_array = InvShiftRows(state_array)

                # Inv Sub Bytes
                state_array = InvSubBytes(state_array)

                # XOR with initial Round Key
                key_chunk = self.key_schedule[0] + self.key_schedule[1] + self.key_schedule[2] + self.key_schedule[3]
                key_array = create_state_array(key_chunk)
                state_array = add_round_key(state_array, key_array)

                # Write decrypted Block to file
                plaintext_bv = BitVector(size=0)
                for i in range(4):
                    for j in range(4):
                        plaintext_bv += state_array[j][i]

                # Convert BitVector to sttring
                decrypted_text += plaintext_bv.get_text_from_bitvector()

        with open(decrypted, 'w') as out_fp:
            out_fp.write(decrypted_text)

    def ctr_aes_image(self, iv:BitVector, image_file:str, enc_image:str) -> None:
        # Read the input image file
        with open(image_file, 'rb') as in_fp:
            image_data = in_fp.read()

        # Open the output encrypted image file
        with open(enc_image, 'wb') as out_fp:
            # Write the image header first
            out_fp.write(image_data[:15])

            # Initialize the counter
            counter = iv.deep_copy()

            # Iterate over the image data in blocks of 16 bytes
            for i in range(15, len(image_data), 16):
                # Encrypt the counter to generate the keystream
                keystream = self._encrypt_block(counter)

                # XOR the keystream with the plaintext block
                plaintext_block = BitVector(rawbytes=image_data[i:i+16])
                ciphertext_block = plaintext_block ^ keystream

                # Write the ciphertext block to the output image file
                ciphertext_block.write_to_file(out_fp)

                # Increment the counter
                counter_int = convert(counter)
                counter_int += 1
                counter = BitVector(intVal=counter_int, size=128)

    def x931(self, v0:BitVector, dt:BitVector, totalNum:int, outfile:str) -> None:
        vj = v0
        with open(outfile, 'w') as f:
            for _ in range(totalNum):
                # Random Number is Ri = E(*K, vj ^ E(*K, DT))
                i = self._encrypt_block(dt)
                r = self._encrypt_block(vj ^ i)

                # Write random number to file
                f.write(str(int(str(r), 2)) + '\n')

                # Next seed is Vj+1 = E(*K, Ri ^ E(*K, DT))
                vj = self._encrypt_block(r ^ i)

    def _encrypt_block(self, plaintext_bv):
        # Convert the plaintext block to a state array
        state_array = create_state_array(plaintext_bv)

        # XOR the first four words of the key schedule with the state array
        key_chunk = self.key_schedule[0] + self.key_schedule[1] + self.key_schedule[2] + self.key_schedule[3]
        key_array = create_state_array(key_chunk)
        state_array = add_round_key(state_array, key_array)

        # Perform AES encryption rounds
        for i in range(1,14):
            # Substitute Bytes
            state_array = SubBytes(state_array)

            # Shift Rows
            state_array = ShiftRows(state_array)

            # Mix Columns
            state_array = MixColumns(state_array)

            # Add Key
            key_chunk = self.key_schedule[4*i] + self.key_schedule[(4*i) + 1] + self.key_schedule[(4*i) + 2] + self.key_schedule[(4*i) + 3]
            key_array = create_state_array(key_chunk)
            state_array = add_round_key(state_array, key_array)
        
        # Final Round without MixColumns
        # Substitute Bytes
        state_array = SubBytes(state_array)

        # Shift Rows
        state_array = ShiftRows(state_array)

        # Add Key
        key_chunk = self.key_schedule[56] + self.key_schedule[57] + self.key_schedule[58] + self.key_schedule[59]
        key_array = create_state_array(key_chunk)
        state_array = add_round_key(state_array, key_array)

        # Convert state array to BitVector
        ciphertext_bv = BitVector(size=0)
        for i in range(4):
            for j in range(4):
                ciphertext_bv += state_array[j][i]
        
        return ciphertext_bv
    

if __name__ == "__main__":
    cipher = AES(keyfile = sys.argv[3])

    if sys.argv[1] == "-e":
        cipher.encrypt(plaintext=sys.argv[2], ciphertext=sys.argv[4])
    elif sys.argv[1] == "-d":
        cipher.decrypt(ciphertext=sys.argv[2], decrypted=sys.argv[4])
    elif sys.argv[1] == "-i":
        cipher.ctr_aes_image(iv=BitVector(textstring="counter-mode-ctr"), image_file=sys.argv[2], enc_image=sys.argv[4])
    else:
        cipher.x931(v0=BitVector(textstring="counter-mode-ctr"), dt=BitVector(intVal=501,size=128), totalNum=int(sys.argv[2]), outfile=sys.argv[4])

