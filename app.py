import time

class Client:

    def run(self):
        print("start running")
        while True:
            self.single_run()
            time.sleep(5)

    def single_run(self):
        print("single running")

if __name__=="__main__":
    client = Client()
    client.run()
