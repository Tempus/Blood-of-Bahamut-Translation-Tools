#include <stdio.h>
#include <string.h>

unsigned short data1;
unsigned short data2;

void setup_checksum() {
    data1 = 0x8048;
    data2 = 0;
}

void add_byte_to_checksum(char data) {
    int counter;
    int temp;
    int r1, r3;
    r3 = data2;
    
    for (counter = 0; counter < 8; counter++) {
        temp = data ^ r3;
        r1 = r3 << 0xF;
        
        if ((temp & 1) != 0) r3 = (r1 >> 0x10) ^ data1;
        if ((temp & 1) == 0) r3 = r1 >> 0x10;
        
        data = (data >> 1) & 0xFF;
    }
    
    data2 = r3;
}

unsigned short bob_checksum(char *data, int size) {
    int counter;
    char temp;
    
    setup_checksum();
    
    if (size <= 0) return data2;
    
    for (counter = 0; counter < size; counter++) {
        temp = *(data++);
        add_byte_to_checksum(temp);
    }
    
    return data2;
}

int main(int argc, char **argv) {
    FILE *savefile;
    long size;
    unsigned int magic;
    unsigned short real_checksum, calc_checksum;
    char buffer[0x10C];
    
    if (argc < 2) {
        printf("No file specified!\n");
        printf("Run: ./bob_checksum <filename>\n");
        return 1;
    }
    
    printf("Opening file %s\n", argv[1]);
    
    savefile = fopen(argv[1], "rb");
    if (savefile == 0) {
        printf("File can't be opened!\n");
        return 1;
    }
    
    fseek(savefile, 0, SEEK_END);
    size = ftell(savefile);
    rewind(savefile);
    
    printf("File size: 0x%x bytes\n", size);
    if (size < 0x10C) {
        printf("File is way too small!\n");
        return 1;
    }
    
    fread(buffer, 1, 0x10C, savefile);
    
    if (memcmp(buffer, "GIGTSAVE", 8) != 0) {
        printf("Not a BOB savefile!\n");
        return 1;
    }
    
    real_checksum = buffer[0xC] | (buffer[0xD] << 8);
    calc_checksum = bob_checksum(buffer+0x10, 0xFC);
    
    printf("Savefile checksum: %04x\n", real_checksum);
    printf("Calculated checksum: %04x\n", calc_checksum);
    
    return 0;
}
