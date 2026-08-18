import subprocess
import time
import csv
import re
import argparse

def parse_mem(mem_str):
    """Convert memory string like '120.5MiB' or '1.2GiB' to MB float"""
    mem_str = mem_str.split(' / ')[0].strip() # Handle "120MiB / 4GiB"
    if "GiB" in mem_str:
        return float(mem_str.replace("GiB", "")) * 1024
    elif "MiB" in mem_str:
        return float(mem_str.replace("MiB", ""))
    elif "KiB" in mem_str:
        return float(mem_str.replace("KiB", "")) / 1024
    elif "B" in mem_str:
        return float(mem_str.replace("B", "")) / (1024*1024)
    return 0.0

def parse_cpu(cpu_str):
    """Convert CPU string like '0.50%' to float"""
    return float(cpu_str.replace("%", ""))

def run_monitor(duration_sec, output_file):
    print(f"Starting resource monitor for {duration_sec} seconds...")
    print(f"Writing results to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Container', 'CPU_Percent', 'RAM_MB']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        start_time = time.time()
        while time.time() - start_time < duration_sec:
            try:
                # Get docker stats for our 3 containers
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"],
                    capture_output=True, text=True
                )
                
                timestamp = int(time.time())
                for line in result.stdout.strip().split('\n'):
                    if not line or 'food_buddy_edge' not in line:
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 3:
                        name = parts[0]
                        cpu = parse_cpu(parts[1])
                        ram = parse_mem(parts[2])
                        
                        writer.writerow({
                            'Timestamp': timestamp,
                            'Container': name.replace('food_buddy_edge-', ''),
                            'CPU_Percent': cpu,
                            'RAM_MB': ram
                        })
            except Exception as e:
                print(f"Error fetching stats: {e}")
                
            time.sleep(1)
            
    print("Monitoring completed. Analyzing results...")
    analyze_csv(output_file)

def analyze_csv(input_file):
    stats = {}
    
    with open(input_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            container = row['Container']
            if container not in stats:
                stats[container] = {'cpu': [], 'ram': []}
                
            stats[container]['cpu'].append(float(row['CPU_Percent']))
            stats[container]['ram'].append(float(row['RAM_MB']))
            
    print("\n" + "="*50)
    print("RESOURCE USAGE SUMMARY")
    print("="*50)
    print(f"{'Container':<15} | {'Max RAM (MB)':<15} | {'Avg CPU (%)':<15} | {'Max CPU (%)':<15}")
    print("-" * 65)
    
    for container, data in stats.items():
        if not data['cpu']: continue
        
        max_ram = max(data['ram'])
        avg_cpu = sum(data['cpu']) / len(data['cpu'])
        max_cpu = max(data['cpu'])
        
        print(f"{container:<15} | {max_ram:<15.2f} | {avg_cpu:<15.2f} | {max_cpu:<15.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docker Resource Monitor")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Duration to monitor in seconds")
    parser.add_argument("-o", "--output", type=str, default="resource_log.csv", help="Output CSV file")
    args = parser.parse_args()
    
    run_monitor(args.duration, args.output)
