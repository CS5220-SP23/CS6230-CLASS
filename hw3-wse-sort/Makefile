.PHONY: clean run debug all small hskew vskew perf


all: run

run: small

small:
	# Px Py dx dy options
	@./commands_wse3.sh 2 2 8 8

hskew:
	# Px Py dx dy options
	@./commands_wse3.sh 2 8 8 8

vskew:
	# Px Py dx dy options
	@./commands_wse3.sh 8 2 8 8

pelarge:
	# Px Py dx dy options
	@./commands_wse3.sh 2 2 24 24

perf:
	@mkdir -p perflogs
	@rm perflogs/* || true
	# Px Py dx dy options
	@PERF=1 ./commands_wse3.sh 2 2 8 8
	# Large PE
	@PERF=1 ./commands_wse3.sh 2 2 64 8 --iters 20000
	@PERF=1 ./commands_wse3.sh 2 2 8 64 --iters 20000
	@PERF=1 ./commands_wse3.sh 2 2 64 64 --iters 20000
	# Large grid
	@PERF=1 ./commands_wse3.sh 32 2 8 8 --iters 20000
	@PERF=1 ./commands_wse3.sh 2 32 64 64 --iters 20000

clean:
	@rm -r out simfab_traces sim.log sim_stats.json simconfig.json wio_flows_tmpdir.* img perflogs &>/dev/null || true

debug:
	@cs_python debug.py

