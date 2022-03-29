import os, struct
from .file_manager import FileManager
from crccheck.crc import CrcKermit

def byte_string_reverse(byte_string):
    reversed_byte_string = ''
    for byte in range(-1, -len(byte_string), -2):
        reversed_byte_string += byte_string[byte - 1] + byte_string[byte]
    return reversed_byte_string

def byte_string_split(byte_string):
    splitted_byte_string_list = []
    i = 0

    splitted_byte_string_list.append(byte_string[0:2])      #0 Frame Length
    splitted_byte_string_list.append(byte_string[2:6])      #1 TagID
    splitted_byte_string_list.append(byte_string[6:14])     #2 PosX
    splitted_byte_string_list.append(byte_string[14:22])    #3 PosY
    splitted_byte_string_list.append(byte_string[22:30])    #4 PosZ
    splitted_byte_string_list.append(byte_string[30:34])    #5 PosQuality
    splitted_byte_string_list.append(byte_string[34:42])    #6 SuperFrameNumber
    splitted_byte_string_list.append(byte_string[42:46])    #7 CRC-16/KERMIT

    for byte in splitted_byte_string_list:
        
        splitted_byte_string_list[i] = byte_string_reverse(byte)
        
        i = i + 1 

    return splitted_byte_string_list

def get_crc(byte_string):
    crc_get = CrcKermit()
    byte_string_to_crc = byte_string[2:-4]
    crc = crc_get.process(bytes.fromhex(byte_string_to_crc))

    return crc.finalhex()

def get_checksum(byte_string):

    byte_string_length = int(len(byte_string[2:-4]))

    if byte_string_length % 2 == 0:
        return byte_string_length/2 
    else:
        print ("Error, invalid frame")
        return 0
        
def get_tagID_from_content(byte_string):
    tag_id = byte_string[2:6]
    return tag_id

def get_tagID_from_filename(filename_string):
    tag_id = filename_string[:4]
    return tag_id

def data_verify(file_name, content):
    archieve_files = next(os.walk(FileManager().archieve_dir))[2]
    
    if file_name in archieve_files:
        file_dir = FileManager().archieve_dir + file_name
        archieved_content = open(file_dir).read()

        if get_tagID_from_content(content) == get_tagID_from_filename(file_name):
            if get_crc(content) == get_crc(archieved_content):
                if get_checksum(content) == get_checksum(archieved_content) == 20:
                    return 1 #Verified OK
                else: 
                    return 2 #Invalid checksum
            else:
                return 3 #Invalid CRC
        else:
            return 4 #tagID doesn't match

def data_decode(received_dict_data):
    keys = list(received_dict_data.keys())

    if len(keys) == 2 and keys[0] == "fileName" and keys[1] == 'fileContent':
        filename = received_dict_data.get("fileName")
        content = received_dict_data.get("fileContent")
        data_verify_feedback = data_verify(filename, content)

        if data_verify_feedback == 1:
            state = 1
            splitted_content = byte_string_split(content)

            position_data = {
                "x": struct.unpack('!f', bytes.fromhex(splitted_content[2]))[0],
                "y": struct.unpack('!f', bytes.fromhex(splitted_content[3]))[0],
                "z": struct.unpack('!f', bytes.fromhex(splitted_content[4]))[0],
                "quality" : int(splitted_content[5], 16),
            }

            decoded_data = {
                "fileName": filename,
                "tagID": int(splitted_content[1],16),
                "position": position_data,
                "superFrameNumber": int(splitted_content[6], 16)
            }

            return decoded_data, state

        elif data_verify_feedback == 2:
            state = 2
            return received_dict_data, state

        elif data_verify_feedback == 3:
            state = 3
            return received_dict_data, state

        elif data_verify_feedback == 4:
            state = 4
            return received_dict_data, state