# utils/ssh_utils.py


# Third-party Libraries
import asyncssh
import asyncio


async def establish_ssh_connection(vps):
    return await asyncssh.connect(
        vps['IP'],
        username=vps['Username'],
        password=vps['Password'],
        known_hosts=None
    )

async def fetch_vps_stats(conn):
    # Fetch VPS stats using the SSH connection
    cpu_details_result = await conn.run('lscpu')
    initial_top_5_processes = await conn.run("ps -eo pid,%cpu,%mem,cmd --sort=-%cpu | head -n 6")

    # Pause for a second to get a change in stats
    await asyncio.sleep(1)

    final_memory_stats = await conn.run('free -h')
    final_disk_stats = await conn.run('df -h /')
    final_top_5_processes = await conn.run("ps -eo pid,%cpu,%mem,cmd --sort=-%cpu | head -n 6")
    initial_cpu_stats = await conn.run('cat /proc/stat | grep "^cpu "')
    final_cpu_stats = await conn.run('cat /proc/stat | grep "^cpu "')

    return {
        "cpu_details": cpu_details_result,
        "initial_top_5": initial_top_5_processes,
        "final_memory": final_memory_stats,
        "final_disk": final_disk_stats,
        "final_top_5": final_top_5_processes,
        "initial_cpu": initial_cpu_stats,
        "final_cpu": final_cpu_stats
    }

async def process_vps_stats(stats, conn):
    # Parsing memory usage
    mem_data = stats['final_memory'].stdout.splitlines()[1].split()
    mem_usage = f"Total: {mem_data[1]}\nUsed: {mem_data[2]}\nFree: {mem_data[3]}\nShared: {mem_data[4]}\nBuff/Cache: {mem_data[5]}\nAvailable: {mem_data[6]}"

    # Parsing disk usage
    disk_data = stats['final_disk'].stdout.splitlines()[1].split()
    disk_usage = f"Size: {disk_data[1]}\nUsed: {disk_data[2]}\nAvail: {disk_data[3]}\nUse%: {disk_data[4]}"

    # Parsing CPU details
    cpu_cores_result = await conn.run('nproc')
    cpu_cores = cpu_cores_result.stdout.strip()
    cpu_data_line = [line for line in stats['cpu_details'].stdout.splitlines() if "Model name" in line][0]
    cpu_data = cpu_data_line.split(":")[1].strip()

    # Fetching CPU usage by comparing two snapshots of /proc/stat
    def extract_cpu_time_parts(cpu_stat_line):
        return [int(value) for value in cpu_stat_line.split()[1:8]]

    initial_values = extract_cpu_time_parts(stats['initial_cpu'].stdout)
    final_values = extract_cpu_time_parts(stats['final_cpu'].stdout)

    prev_idle = initial_values[3] + initial_values[4]
    idle = final_values[3] + final_values[4]

    prev_non_idle = sum(initial_values) - prev_idle
    non_idle = sum(final_values) - idle

    prev_total = prev_idle + prev_non_idle
    total = idle + non_idle

    # Calculate the CPU percentage
    total_difference = total - prev_total
    idle_difference = idle - prev_idle
    cpu_percentage = (total_difference - idle_difference) / total_difference * 100

    cpu_usage = f"Type: {cpu_data}\nCores: {cpu_cores}\nUsage: {cpu_percentage:.2f}%"

    # Parsing top 5 processes
    initial_process_lines = stats['initial_top_5'].stdout.splitlines()[1:]
    final_process_lines = stats['final_top_5'].stdout.splitlines()[1:]

    top_processes = ""
    for i in range(5):
        pid, initial_cpu, initial_mem, *initial_cmd = initial_process_lines[i].split()
        _, final_cpu, final_mem, *final_cmd = final_process_lines[i].split()

        avg_cpu = (float(initial_cpu) + float(final_cpu)) / 2
        avg_mem = (float(initial_mem) + float(final_mem)) / 2
        cmd = " ".join(initial_cmd)

        top_processes += f"{i+1}. PID: {pid} | CPU: {avg_cpu:.2f}% | MEM: {avg_mem:.2f}% | CMD: {cmd}\n"

    return mem_usage, disk_usage, cpu_usage, top_processes