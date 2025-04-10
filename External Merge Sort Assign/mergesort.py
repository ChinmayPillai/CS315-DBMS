#!/usr/bin/env python3
import sys
import math

class ExternalMergesort:
    def __init__(self, input_file, n, k, b, m):
        self.input_file = input_file  # Input File
        self.n = n                    # Total number of keys
        self.k = k                    # Size of each key in bytes
        self.b = b                    # Disk block size in bytes
        self.m = m                    # Memory Size in number of blocks
        
        self.keys_per_block = b // k  # Number of keys that fit in one block
        self.total_blocks = math.ceil(n / self.keys_per_block)  # Total blocks needed for input

        self.disk_seeks = 0
        self.disk_transfers = 0
        
        self.pass_details = []
        
    def read_input_file(self):
        """
            Read the input file for n int keys

            Returns:
                keys: List of n keys
        """
        with open(self.input_file, 'r') as f:
            keys = [int(line.strip()) for line in f if line.strip()]
        return keys[:self.n]
    
    def simulate_disk_read(self, num_blocks=1):
        """
            Simulate reading blocks from disk

            Args:
                num_blocks: Number of blocks to read
        """
        self.disk_seeks += 1
        self.disk_transfers += num_blocks
        
    def simulate_disk_write(self, num_blocks=1):
        """
            Simulate writing blocks to disk

            Args:
                num_blocks: Number of blocks to write    
        """
        self.disk_seeks += 1
        self.disk_transfers += num_blocks
    
    def create_initial_runs(self, keys):
        """
            Create initial sorted runs
            
            Args:
                keys: List of keys to sort
        """

        runs = []       # List of sorted runs
        keys_per_run = self.keys_per_block * self.m  # Keys that fit in memory
        
        # Track disk operations for this phase
        seeks_in_phase = 0
        transfers_in_phase = 0
        
        for i in range(0, len(keys), keys_per_run):
            # Read blocks into memory
            run_keys = keys[i:i+keys_per_run]
            blocks_read = math.ceil(len(run_keys) / self.keys_per_block)
            self.simulate_disk_read(blocks_read)
            seeks_in_phase += 1
            transfers_in_phase += blocks_read
            
            # Sort this run in memory
            run_keys.sort()
            
            # Split the sorted run into blocks
            run_blocks = []
            for j in range(0, len(run_keys), self.keys_per_block):
                block = run_keys[j:j+self.keys_per_block]
                run_blocks.append(block)
            
            runs.append(run_blocks)
            
            # Write sorted run back to disk
            blocks_written = len(run_blocks)
            self.simulate_disk_write(blocks_written)
            seeks_in_phase += 1
            transfers_in_phase += blocks_written
        
        # Record details for this phase
        self.pass_details.append({
            "phase": "Initial Run Creation",
            "num_runs": len(runs),
            "disk_seeks": seeks_in_phase,
            "disk_transfers": transfers_in_phase
        })
        
        return runs
    
    def merge_pass(self, runs, pass_num):
        """
            Perform one merge pass according to the m-way merge algorithm

            Args:
                runs: List of sorted runs to merge
                pass_num: The current merge-pass number        
        """
        new_runs = []
        seeks_in_pass = 0
        transfers_in_pass = 0

        sub_phases = []
        
        # Process runs in groups of (m-1) 
        # i.e perform m-1 way merge on sets of m-1 sorted runs
        for i in range(0, len(runs), self.m - 1):

            sub_phase_seeks = 0
            sub_phase_transfers = 0 

            # Get the runs to merge in this iteration
            runs_to_merge = runs[i:i+self.m-1]
            
            # If there's only one run in this group, no merging needed
            # We can keep the statistics to know when there is only 1 block in the run
            # So we need not read the block to know it 
            if len(runs_to_merge) == 1:
                # Sort inplace in disk so that the logical new_runs is actually in the same place as runs
                # This means no need to read and write this block. It can stay where it is in disk
                new_runs.append(runs_to_merge[0])
                sub_phases.append({
                    "runs_merged": len(runs_to_merge),
                    "disk_seeks": sub_phase_seeks,
                    "disk_transfers": sub_phase_transfers
                })
                continue
            
            # Disk (simulated) store of the block written by output (mth) buffer after merge 
            merged_run_blocks = []

            # m-1 block buffer to hold the blocks to merge
            buffers = []
            # Current position within each buffer
            buffer_indices = []  
            
            for run in runs_to_merge:
                # If the run has blocks left 
                if run:  
                    # Read first block of each run and add it to buffers
                    buffer = run[0]  
                    self.simulate_disk_read()
                    sub_phase_seeks += 1
                    sub_phase_transfers += 1
                    buffers.append(buffer)
                    buffer_indices.append(0)
                    
            # Index to track which block of each sorted run we're currently processing
            run_indices = [0] * len(runs_to_merge)
            
            # Output buffer (m-th block in memory)
            output_buffer = []
            
            # While (m-1) block buffer is not empty
            while any(buffers):

                # Find minimum key across all buffers
                min_val = float('inf')
                min_run_idx = -1
                
                # For each sorted run in buffers
                for j in range(len(buffers)):

                    # If buffer is exhausted
                    if buffer_indices[j] >= len(buffers[j]):
                        continue
                    
                    # Find least value left in buffer and its index
                    least_val = buffers[j][buffer_indices[j]]                    
                    if least_val < min_val:
                        min_val = least_val
                        min_run_idx = j
                
                # If all buffers are exhausted
                if min_run_idx == -1:  
                    break
                
                # Add minimum value to sorted output buffer
                output_buffer.append(min_val)
                # Increment index of sorted run in buffer
                buffer_indices[min_run_idx] += 1
                
                # If output buffer is full, write it to disk
                if len(output_buffer) == self.keys_per_block:
                    # Add 1 sorted block to new sorted run
                    merged_run_blocks.append(output_buffer)
                    self.simulate_disk_write()
                    sub_phase_seeks += 1
                    sub_phase_transfers += 1
                    output_buffer = []
                
                # If the currently used buffer is fully processed due to the operation, 
                # read the next block from that run
                if buffer_indices[min_run_idx] >= len(buffers[min_run_idx]):

                    # Increment the index of block of the currently used sorted run
                    run_indices[min_run_idx] += 1
                    block_idx = run_indices[min_run_idx]
                    
                    # If there are no more blocks in this run to read
                    if block_idx >= len(runs_to_merge[min_run_idx]):
                        # Remove the buffer
                        buffers[min_run_idx] = []
                    else:
                        # Read the next block of the sorted run
                        next_block = runs_to_merge[min_run_idx][block_idx]
                        self.simulate_disk_read()
                        sub_phase_seeks += 1
                        sub_phase_transfers += 1
                        buffers[min_run_idx] = next_block       
                        buffer_indices[min_run_idx] = 0         # Reset the index of the block
            
            # Write any remaining keys in the output buffer
            if output_buffer:
                merged_run_blocks.append(output_buffer)
                self.simulate_disk_write()
                sub_phase_seeks += 1
                sub_phase_transfers += 1
            
            # Add the merged run to the new set of sorted runs
            new_runs.append(merged_run_blocks)

            # Append sub-phase details
            sub_phases.append({
                "runs_merged": len(runs_to_merge),
                "disk_seeks": sub_phase_seeks,
                "disk_transfers": sub_phase_transfers
            })
            
            # Add sub-phase details to pass total
            seeks_in_pass += sub_phase_seeks
            transfers_in_pass += sub_phase_transfers
        
        # Record details for this merge-pass
        self.pass_details.append({
            "phase": f"Merge Pass {pass_num}",
            "num_runs": len(new_runs),
            "disk_seeks": seeks_in_pass,
            "disk_transfers": transfers_in_pass,
            "sub_phases": sub_phases
        })
        
        return new_runs
    
    def sort(self):
        """
            Execute the external mergesort algorithm

            Returns:
                final_sorted_keys: List of sorted keys
        """
        # Read input keys
        keys = self.read_input_file()
        
        # Create initial sorted runs
        runs = self.create_initial_runs(keys)

        # Merge-pass until we have a single run left
        pass_num = 1
        while len(runs) > 1:
            runs = self.merge_pass(runs, pass_num)
            pass_num += 1
        
        # Flatten the final run for output
        final_sorted_keys = []
        for block in runs[0]:
            final_sorted_keys.extend(block)
        
        # Calculate theoretical seeks and transfers
        b = self.total_blocks
        m = self.m
        n = math.ceil(b / m)  # Initial number of sorted runs
        r = math.ceil(math.log(n, m-1)) if m > 2 else math.ceil(math.log(n, 2))
        
        # print(f"\nTheoretical Analysis:")
        # print(f"Total blocks (b): {b}")
        # print(f"Memory blocks (m): {m}")
        # print(f"Initial number of runs (n = ⌈b/m⌉): {n}")
        # print(f"Theoretical merge passes needed (r = ⌈logm−1 n⌉): {r}")
        # print(f"Theoretical block transfers: {2*b*r + 2*b}")
        # print(f"Theoretical disk seeks (worst case): {2*n + 2*b*r}")
        
        return final_sorted_keys
    
    def print_output(self):
        """
            Print the required output details    
        """
        total_seeks = self.disk_seeks
        total_transfers = self.disk_transfers
        
        print(f"\n\nNumber of merge passes: {len(self.pass_details) - 1}")
        
        print("\nPhase details:")
        for phase_info in self.pass_details:
            print(f"- {phase_info['phase']}")
            print(f"  Number of sorted runs left after this pass: {phase_info['num_runs']}")
            print(f"  Disk seeks: {phase_info['disk_seeks']}")
            print(f"  Disk transfers: {phase_info['disk_transfers']}")
            
            # Print sub-phase details for merge passes
            if 'sub_phases' in phase_info:
                print(f"  Sub-phases:")
                for i, sub_phase in enumerate(phase_info['sub_phases']):
                    print(f"    Sub-phase {i+1} (merging {sub_phase['runs_merged']} runs):")
                    print(f"      Disk seeks: {sub_phase['disk_seeks']}")
                    print(f"      Disk transfers: {sub_phase['disk_transfers']}")
        
        print("\nTotal disk operations:")
        print(f"Total disk seeks: {total_seeks}")
        print(f"Total disk transfers: {total_transfers}")


    
# Check for proper input, else print usage
if len(sys.argv) != 6:
    print("Usage: ./program input-file.txt n k b m")
    print("  input-file.txt: File containing keys (one per line)")
    print("  n: Total number of keys")
    print("  k: Size of each key in bytes")
    print("  b: Disk block size in bytes")
    print("  m: Memory size in number of blocks")
    exit(1)

# Get input parameters
input_file = sys.argv[1]
n = int(sys.argv[2])
k = int(sys.argv[3])
b = int(sys.argv[4])
m = int(sys.argv[5])

# External mergesort
sorter = ExternalMergesort(input_file, n, k, b, m)
sorted_keys = sorter.sort()

sorter.print_output()

# Write the sorted keys
with open("sorted_output.txt", 'w') as f:
    for key in sorted_keys:
        f.write(f"{key}\n")
