import sys
import getopt
from src import SpyWrapper

def main():
	try:
		options, remainder = getopt.getopt(sys.argv[1:], 'c:p:o:v',
		                                   ['config=',
			                                'profile=',
			                                'output=',
			                                'verbose'])
	except getopt.GetoptError as err:
		print('ERROR:', err)
		sys.exit(1)

	verbose = False
	config_file = "cfg/default_dwld_cfg.INI"
	profile = "DEFAULT"
	for opt, arg in options:
		if opt in ('-c', '--config'):
			config_file = arg
		elif opt in ('-p', '--profile'):
			profile = arg
		elif opt in ('-v', '--verbose'):
			verbose = True

	man = SpyWrapper.from_INI(config_file, selector=profile)
	man.get_ALL(dbg=verbose)
	if verbose: print("\nExporting downloaded data to json file.")
	man.export_data_to_json()

if __name__ == "__main__":
	main()

