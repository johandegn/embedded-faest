#!/usr/bin/env python3

# Load data from test/saved-results/access-pattern into array
def load_file_into_array(filename):
    with open(f"test/saved-results/access-pattern/{filename}", 'r') as file:
        data = file.readlines()
        #convert data to int
        data = [int(x.strip()) for x in data]
        return data

# find largest value in data
def find_largest(data):
    largest = 0
    for i in range(0, len(data)):
        if data[i] > largest:
            largest = data[i]
    return largest

# Go over data from file and compute number of recomputation
def compute_recomputation(data, cache_size, largest):
    start_idx = 0
    l = 1600 # 128
    #l = 3264 #192
    #l = 4000  # 256  
    recomputation = 1
    for i in range(0, len(data)):
        if (data[i] > start_idx + cache_size or data[i] < start_idx):
            recomputation += 1
            if (data[i] > l):
                start_idx = data[i] - cache_size
            elif (data[i] + cache_size < largest):
                start_idx = data[i]
            else:
                start_idx = largest - cache_size
    if (recomputation > 1):
        recomputation += 2
    return recomputation


# Main function
if __name__ == '__main__':
    # Load data from file
    variant = "128"
    data = load_file_into_array(f"vk_box_cache/{variant}.txt")
    largest = find_largest(data)
    # Go over all cache sizes from 19 to largest and store in an array
    recomputation = []
    for i in range(19, largest+1):
        recomputation.append(compute_recomputation(data, i, largest))

    # Write recomputation to file
    with open(f"test/saved-results/access-pattern/vk_box_cache/comp-{variant}.txt", 'w') as file:
        for i in range(0, len(recomputation)):
            file.write(f"{recomputation[i]}\n")    

