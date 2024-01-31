#include "faest_test.h"

int main(void) {
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    unsigned char sk[CRYPTO_SECRETKEYBYTES];
    if (crypto_sign_keypair(pk, sk) == -1)
        return 1;

    return write_pk(pk) || write_sk(sk);
}
