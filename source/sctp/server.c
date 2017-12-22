#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/sctp.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <netdb.h>
#include <unistd.h>

int main(){
  struct sockaddr_in client;
  int sock;
  // создание сокета
  if((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_SCTP)) == -1){
    printf("Error create socket!\n");
    return -1;
  }

  // настройка канала
  struct sctp_initmsg initmsg;
  initmsg.sinit_num_ostreams = 3; // входные потоки
  initmsg.sinit_max_instreams = 3; // выходные потоки
  initmsg.sinit_max_attempts = 2; // максимальное количество попыток
  setsockopt(sock, IPPROTO_SCTP, SCTP_INITMSG, &initmsg, sizeof(initmsg));

  // структура для описания адресов сервера
  struct addrinfo *res, hints;
  hints.ai_family = AF_INET;
  hints.ai_protocol = IPPROTO_SCTP;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = AI_ADDRCONFIG | AI_V4MAPPED;
  getaddrinfo("10.10.2.2", "2016", &hints, &res);
  getaddrinfo("10.10.4.2", "2017", &hints, &res);

  // 
  struct sockaddr_storage *connect = NULL;
  int cc = 0, count = 0;
  for(; res; res = res->ai_next){
    connect = realloc(connect, cc + res->ai_addrlen);
    memcpy((char*)connect + cc, res->ai_addr, res->ai_addrlen);
    count++;
    cc += res->ai_addrlen;
  }
  // связка
  if(sctp_bindx(sock, (struct sockaddr*)connect, count, SCTP_BINDX_ADD_ADDR) == -1){
    perror("Error stcp_bindx");
    return -1;
  }

  // объявляем очередь
  if(listen(sock,5)==-1){
    printf("Error listen!\n");
    return -1;
  }
  int newsock;
  char buffer[512];
  int clnlen = sizeof(client), flags;
  if((newsock = accept(sock, (struct sockaddr*)&client, &clnlen)) == -1){ // принимаем соединение от клиента
    printf("Error accept!\n");
    return -1;
  }
  printf("Новый клиент!\n");
  while(1){
    bzero((void*)&buffer, sizeof(buffer));
    struct sctp_sndrcvinfo sndrcvinfo; // информация о пересылке
    if(sctp_recvmsg(newsock, (void*)buffer, sizeof(buffer), (struct sockaddr*)NULL, 0, &sndrcvinfo, &flags) == -1){ // принимаем сообщение от клиента
      perror("Error sctp_recvmsg!");
      return -1;
    }
    printf(">>%s\n",buffer);
  }
  close(newsock); // закрываем связь с клиентом
  close(sock); // закрываем сокет сервера
  return 0;
}
