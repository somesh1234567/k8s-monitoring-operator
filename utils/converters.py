# Helper function to convert the memory in Ki to Mb
def convert_memory(memory_str):
    if memory_str.endswith('Ki'):
        return int(memory_str[:-2]) / 1024
    return 0

# Helper function to convert the CPU in millicores
def convert_cpu(cpu_str):
    if cpu_str.endswith('m'):
        return int(cpu_str[:-1])
    elif cpu_str.isdigit():
        return int(cpu_str) * 1000
    return 0