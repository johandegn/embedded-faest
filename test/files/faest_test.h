#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdbool.h>
#include "api.h"

#define MSG "This is the message to sign."
#define MSG_LEN 29ULL

int write_pk(const unsigned char *pk) {
    FILE *file = fopen(CRYPTO_ALGNAME "_pk", "wb");
    if (file == NULL)
        return 1;

    if (fwrite(pk, 1, CRYPTO_PUBLICKEYBYTES, file) != CRYPTO_PUBLICKEYBYTES) {
        fclose(file);
        return 1;
    }
    return fclose(file);
}

int write_sk(const unsigned char *sk) {
    FILE *file = fopen(CRYPTO_ALGNAME "_sk", "wb");
    if (file == NULL)
        return 1;

    if (fwrite(sk, 1, CRYPTO_SECRETKEYBYTES, file) != CRYPTO_SECRETKEYBYTES) {
        fclose(file);
        return 1;
    }
    return fclose(file);
}

int read_pk(unsigned char *pk) {
    FILE *file = fopen(CRYPTO_ALGNAME "_pk", "rb");
    if (file == NULL)
        return 1;

    if (fread(pk, 1, CRYPTO_PUBLICKEYBYTES, file) != CRYPTO_PUBLICKEYBYTES) {
        fclose(file);
        return 1;
    }
    return fclose(file);
}

int read_sk(unsigned char *sk) {
    FILE *file = fopen(CRYPTO_ALGNAME "_sk", "rb");
    if (file == NULL)
        return 1;

    if (fread(sk, 1, CRYPTO_SECRETKEYBYTES, file) != CRYPTO_SECRETKEYBYTES) {
        fclose(file);
        return 1;
    }
    return fclose(file);
}

int write_signature(const unsigned char *sm) {
    FILE *file = fopen(CRYPTO_ALGNAME "_signature", "wb");
    if (file == NULL)
        return 1;

    if (fwrite(sm, 1, CRYPTO_BYTES + MSG_LEN, file) != CRYPTO_BYTES + MSG_LEN) {
        fclose(file);
        return 1;
    }

    return fclose(file);
}

int read_signature(unsigned char *sm) {
    FILE *file = fopen(CRYPTO_ALGNAME "_signature", "rb");
    if (file == NULL)
        return 1;

    if (fread(sm, 1, CRYPTO_BYTES + MSG_LEN, file) != CRYPTO_BYTES + MSG_LEN) {
        fclose(file);
        return 1;
    }

    return fclose(file);
}
