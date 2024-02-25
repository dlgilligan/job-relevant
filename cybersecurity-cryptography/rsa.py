import sys
from PrimeGenerator import *
from solve_pRoot import *

# Steps for RSA algorithm
#   1. Generate two different primes p and q
#   2. Calculate the modulus n = p x q
#   3. Calculate the totient phi(n) = (p - 1) x (q - 1)
#   4. Select for public exponent an integer e such that 1 < e < phi(n) and gcd(phi(n),e) = 1
#   5. Calculate for the private exponent a value for d such that d = e^-1 mod phi(n)
#   6. Public Key = [e,n]
#   7. Private Key = [d,n]

class RSA():
    def __init__(self, e) -> None:
        self.e = e      # Public Key
        self.n = None   # Modulus
        self.d = None   # Private Key
        self.p = None   # Prime 1
        self.q = None   # Prime 2

    def generate_primes(self) -> None:
        # Create an instance of the prime generator class
        prime_gen = PrimeGenerator(bits=128, debug=False)

        # Initialize p and q to invalid values to enter the loop
        self.p = 0
        self.q = 0

        while True:
            # Ensure p and q satisfy the conditions
            while self.p == self.q or (self.p - 1) % self.e == 0 or (self.q - 1) % self.e == 0:
                self.p = prime_gen.findPrime()
                self.q = prime_gen.findPrime()

                # Ensure the two left most bits are set
                self.p |= (1 << 127)
                self.q |= (1 << 127)
        
            # Check if conditions (1) and (3) are set
            if (self.p & (1 << 126)) and (self.q & (1 << 126)):
                # Check if conditions (2) is met
                if self.p != self.q:
                    # Check if condition (4) is met
                    if self.are_coprime(self.p - 1, self.e) and self.are_coprime(self.q - 1, self.e):
                        break

    def calculate_n_and_d(self) -> None:
        self.n = self.p * self.q 
        phi_n = (self.p - 1) * (self.q - 1)
        self.d = self.modular_inverse(self.e, phi_n)

    def generate_keys(self, p_file:str, q_file:str) -> None:
        self.generate_primes()
        self.calculate_n_and_d()

        # Write p and q to file
        with open(p_file, 'w') as f:
            f.write(str(self.p))
        with open(q_file, 'w') as f:
            f.write(str(self.q))

    def are_coprime(self, a:int, b:int) -> bool:
        while b:
            a, b = b, a % b
        return a == 1

    def modular_inverse(self, a:int, m:int) -> int:
        m0, x0, x1 = m, 0, 1
        while a > 1:
            q = a // m
            m, a = a % m, m
            x0, x1 = x1 - q * x0, x0
        return x1 + m0 if x1 < 0 else x1

    def pad(self, plaintext: str) -> str:
        padded_plaintext = plaintext
        if len(plaintext) % 16 != 0:
            padding_length = 16 - (len(plaintext) % 16)
            padded_plaintext += '\x00' * padding_length
        return padded_plaintext

    def unpad(self, plaintext: str) -> str:
        return plaintext.rstrip('\x00')

    def encrypt(self, plaintext:str, ciphertext:str, p_file:str, q_file:str) -> None:
        # Get p and q from file
        with open(p_file, 'r') as f:
            self.p = int(f.read().strip())
        with open(q_file, 'r') as f:
            self.q = int(f.read().strip())

        # Calculate n and d
        self.calculate_n_and_d()

        # Read plaintext from file
        with open(plaintext, 'r') as f:
            plain_text = f.read().strip()

        # Pad plaintext and split into blocks
        plain_text = self.pad(plain_text)
        blocks = [plain_text[i:i+16] for i in range(0, len(plain_text), 16)]

        # Encrypt each block individually
        encrypted_blocks = []
        for block in blocks:
            # Convert the block of ASCII values to a single integer
            num = int.from_bytes(block.encode(), 'big')
            # Apply rsa encryption
            encrypted_num = pow(num, self.e, self.n)
            encrypted_blocks.append(encrypted_num)
        
        # Write encrypted blocks to file
        with open(ciphertext, 'w') as f:
            f.write('\n'.join(hex(block)[2:] for block in encrypted_blocks))

    def decrypt(self, ciphertext:str, recovered_plaintext:str, p_file:str, q_file:str) -> None:
        # Get p and q from file
        with open(p_file, 'r') as f:
            self.p = int(f.read().strip())
        with open(q_file, 'r') as f:
            self.q = int(f.read().strip())

        # Calculate n and d
        self.calculate_n_and_d()

        # Read ciphertext from file
        with open(ciphertext, 'r') as f:
            encrypted_blocks = f.read().splitlines()

        # Decrypt each block individually
        decrypted_blocks = []
        for block in encrypted_blocks:
            encrypted_num = int(block, 16)
            # Apply RSA decryption
            decrypted_num = pow(encrypted_num, self.d, self.n)
            block_bytes = decrypted_num.to_bytes((decrypted_num.bit_length() + 7) // 8, 'big')
            decrypted_blocks.append(block_bytes)

        # Join decrypted blocks into a single plaintext string
        plaintext_bytes = b''.join(decrypted_blocks)

         # Write decrypted plaintext to file
        with open(recovered_plaintext, 'wb') as f:
            f.write(plaintext_bytes)


if __name__ == "__main__":
    rsa = RSA(e=65537)

    if len(sys.argv) == 4 and sys.argv[1] == "-g":
        rsa.generate_keys(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 6 and sys.argv[1] == "-e":
        rsa.encrypt(sys.argv[2], sys.argv[5], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 6 and sys.argv[1] == "-d":
        rsa.decrypt(sys.argv[2], sys.argv[5], sys.argv[3], sys.argv[4])
    else:
        print("Invalid command-line arguments.")
