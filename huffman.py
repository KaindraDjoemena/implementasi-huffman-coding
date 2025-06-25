import os
import heapq

class HuffmanCoding:
    def __init__(self, path):
        self.path = path
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}
        self.data_start_pos = 0
    
    # implementasi node untuk priotrity queue
    class HeapNode:
        def __init__(self, char, freq):
            self.char = char
            self.freq = freq
            self.left = None
            self.right = None

        def __lt__(self, other):
            return self.freq < other.freq
        
        def __eq__(self, other):
            if other == None:
                return False
            if not isinstance(other, HeapNode):
                return False
            return self.freq == other.freq

    def build_frequency_dict(self, text):
        # menghitung frekuensi karakter
        frequency = {}
        for c in text:
            if not c in frequency:
                frequency[c] = 0
            frequency[c] += 1
        return frequency

    def build_heap(self, frequency):
        # membuat priority queue
        for key in frequency:
            node = self.HeapNode(key, frequency[key])
            heapq.heappush(self.heap, node)

    def merge_nodes(self):
        # menggabungkan node untuk membuat Huffman tree
        while (len(self.heap) > 1):
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)

            merged = self.HeapNode(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2

            heapq.heappush(self.heap, merged)

    def make_codes_helper(self, node, current_code):
        if node == None:
            return
        
        if node.char != None:
            self.codes[node.char] = current_code
            self.reverse_mapping[current_code] = node.char
        
        self.make_codes_helper(node.left, current_code + "0")
        self.make_codes_helper(node.right, current_code + "1")

    def make_codes(self):
        # membuat kode Huffman untuk tiap karakter
        root = heapq.heappop(self.heap)
        current_code = ""
        self.make_codes_helper(root, current_code)

    def get_encoded_text(self, text):
        # mengencode teks menggunakan kode Huffman
        encoded_text = ""
        for char in text:
            encoded_text += self.codes[char]
        return encoded_text

    def pad_encoded_text(self, encoded_text):
        # menambahkan padding pada encoded text
        extra_padding = 8 - len(encoded_text) % 8
        if extra_padding == 8:
            extra_padding = 0
            
        padded_info = "{0:08b}".format(extra_padding)  # padding dalam binary
        
        # Add padding bits
        padded_encoded_text = ""
        padded_encoded_text = padded_info + encoded_text
        
        # Add extra padding
        for i in range(extra_padding):
            padded_encoded_text += "0"
            
        return padded_encoded_text

    def get_byte_array(self, padded_encoded_text):
        # mengubah padded encoded text menjadi byte 
        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i+8]
            b.append(int(byte, 2))
        return b

    def compress(self):
        # mengcompress file
        filename, file_extension = os.path.splitext(self.path)
        output_path = filename + ".bin"
        
        with open(self.path, 'r') as file, open(output_path, 'wb') as output_file:
            text = file.read()
            text = text.rstrip()
            
            if not text:
                print("Empty file, nothing to compress")
                return output_path

            frequency = self.build_frequency_dict(text)
            self.build_heap(frequency)
            self.merge_nodes()
            self.make_codes()

            # Wheader untuk kode huffman
            num_chars = len(self.codes)
            output_file.write(num_chars.to_bytes(1, byteorder='big'))
            
            # Write the character map in a simple format
            for char, code in self.codes.items():
                # Write character (1 byte)
                char_byte = ord(char) if len(char) == 1 else 0
                output_file.write(char_byte.to_bytes(1, byteorder='big'))
                
                # Write code length (1 byte)
                output_file.write(len(code).to_bytes(1, byteorder='big'))
                
                # Write code in bytes (pad to full bytes)
                code_bits = code.ljust((len(code) + 7) // 8 * 8, '0')
                for i in range(0, len(code_bits), 8):
                    byte = code_bits[i:i+8]
                    output_file.write(int(byte, 2).to_bytes(1, byteorder='big'))
            
            # menulis data terkompresi dalam file
            encoded_text = self.get_encoded_text(text)
            padded_encoded_text = self.pad_encoded_text(encoded_text)
            byte_array = self.get_byte_array(padded_encoded_text)
            output_file.write(bytes(byte_array))

        print("Compressed")
        return output_path

    def remove_padding(self, bit_string):
        # menghapus padding
        padded_info = bit_string[:8]
        extra_padding = int(padded_info, 2)

        # Remove the padding info (first 8 bits)
        bit_string = bit_string[8:]
        
        # Remove the extra padding bits from the end
        if extra_padding > 0:
            encoded_text = bit_string[:-extra_padding]
        else:
            encoded_text = bit_string
            
        return encoded_text

    def decode_text(self, encoded_text):
        current_code = ""
        decoded_text = ""

        for bit in encoded_text:
            current_code += bit
            if current_code in self.reverse_mapping:
                character = self.reverse_mapping[current_code]
                decoded_text += character
                current_code = ""
                
        return decoded_text

    def load_codes_from_file(self):
        # Load Huffman codes from the beginning of the compressed file
        try:
            with open(self.path, 'rb') as file:
                # Read the number of characters in the map (1 byte)
                num_chars = int.from_bytes(file.read(1), byteorder='big')
                
                # Read each character mapping
                for _ in range(num_chars):
                    # Read character ASCII value (1 byte)
                    char_byte = int.from_bytes(file.read(1), byteorder='big')
                    char = chr(char_byte) if char_byte > 0 else ''
                    
                    # Read code length (1 byte)
                    code_length = int.from_bytes(file.read(1), byteorder='big')
                    
                    # Calculate how many bytes we need to read for this code
                    bytes_needed = (code_length + 7) // 8
                    
                    # Read the code bytes
                    code = ""
                    for _ in range(bytes_needed):
                        byte = int.from_bytes(file.read(1), byteorder='big')
                        bits = bin(byte)[2:].rjust(8, '0')
                        code += bits
                    
                    # Trim to the actual code length
                    code = code[:code_length]
                    
                    # Add to the reverse mapping
                    self.reverse_mapping[code] = char
                
                # Store where the actual compressed data begins
                self.data_start_pos = file.tell()
                
                return True
                
        except Exception as e:
            print(f"Error loading codes from file: {e}")
            return False

    def decompress(self):
        # mendekompres file
        filename, file_extension = os.path.splitext(self.path)
        output_path = filename + "_decompressed" + ".txt"
        
        # Load the codes first from the compressed file
        if not self.load_codes_from_file():
            print("Failed to load codes for decompression.")
            return None

        with open(self.path, 'rb') as file, open(output_path, 'w') as output_file:
            # Skip to where the actual compressed data starts
            file.seek(self.data_start_pos)
            
            # Read the compressed data
            byte_data = file.read()
            
            # Convert to bit string
            bit_string = ""
            for byte in byte_data:
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits

            # Remove padding and decode
            encoded_text = self.remove_padding(bit_string)
            decoded_text = self.decode_text(encoded_text)
            output_file.write(decoded_text)
        
        print("Decompressed")
        return output_path


if __name__ == "__main__":
    # kompresi
    h = HuffmanCoding("test.txt")
    compressed_file = h.compress()
    print(f"File compressed to: {compressed_file}")
    
    # dekompresi:
    # print(f"Decompressing {"text.bin"}...")
    h_decompress = HuffmanCoding("test.bin")
    decompressed_file = h_decompress.decompress()
    print(f"File decompressed to: {decompressed_file}")