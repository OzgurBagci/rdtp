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

  // создаем сокет
  int sock;
  if((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_SCTP)) == -1){
    printf("Error create!\n");
    return -1;
  }

  // настройка канала
  struct sctp_initmsg initmsg;
  memset(&initmsg, 0, sizeof(initmsg));
  initmsg.sinit_num_ostreams = 3; // выходные потоки
  initmsg.sinit_max_instreams = 3; // входные потоки
  initmsg.sinit_max_attempts = 2; // количество попыток
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
  // соединение с сервером
  if(sctp_connectx(sock, (struct sockaddr*)connect, count, 0) == -1){ 
    perror("Error sctp_connectx");
    exit(-1);
  }

  // отправка и прием сообщения
  while(1){
    char buf[512] = "Hello!";
    sctp_sendmsg(sock, (void*)buf, (size_t)strlen(buf), NULL, 0, 0, 0, 0, 0, 0); // 3й сконца - номер потока
    sleep(2);
  }
  close(sock);
  return 0;
}
