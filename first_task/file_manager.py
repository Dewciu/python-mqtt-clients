import os

class FileManager:
    

    def __init__(self):
        self.in_dir = 'first_task_v2/files/in_folder/'
        self.archieve_dir = 'first_task_v2/files/archieve_folder/'
        self.json_dir = 'first_task_v2/files/json_folder/'
        self.error_dir = 'first_task_v2/files/error_folder/'
        self.raw_data_set = []
        self.raw_data = {"fileName": "", "fileContent": ""}
    

    def get_raw_data(self):
        in_files = next(os.walk(self.in_dir))[2]
        for file in in_files:
            file_dir = self.in_dir + file
            content = open(file_dir).read()
            self.raw_data = {"fileName" : file , "fileContent" : content}
            self.raw_data_set.append(self.raw_data)
            # print(self.raw_data_set)
            os.replace(file_dir, self.archieve_dir + file)
            # time.sleep(1)
        return self.raw_data_set

    def create_json_file(self, data):
        file = open(self.json_dir + data.get("fileName"), mode="x")
        file.write(str(data))
    
    def create_error_file(self, data):
        file = open(self.error_dir + data.get("fileName"), mode="x")
        file.write(str(data))