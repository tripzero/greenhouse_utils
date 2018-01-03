from thermalobject import Water, Soil, Air, c_to_kelvin, kelvin_to_c
import json

def cooling_loop(transfer_medium, energy_to_sink, max_tube_length, tube_diameter, soil_temp, flow_rate, verbose = False):

	soil = Soil(mass=9999999999, temperature=soil_temp-1)

	seconds = 999
	length = 0
	time = flow_rate
	energy = 0
	startTemp = transfer_medium.temperature

	while  abs(energy) < (energy_to_sink * time) and length < max_tube_length:
		length += 1

		if verbose:
			print("trying tubing length: {}".format(length))
			print("{} temp: {}C".format(transfer_medium, kelvin_to_c(transfer_medium.temperature)))
			print("{} mass: {}g".format(transfer_medium, transfer_medium.mass))

		d = tube_diameter
		surface_area = 2 * 3.1415 * (d/2) * length + 2* 3.1415 * ((d/2) * (d/2))

		tube_volume = 3.1415 * ((d/2) * (d/2)) * length # m^3

		transfer_medium.mass = tube_volume * transfer_medium.density
		transfer_medium.temperature = startTemp

		time = tube_volume / (flow_rate / 1000)

		if verbose:
			print("time to move all medium: {}".format(time))

		#transfer_medium.energy += (energy_to_sink * time)

		soil.temperature = soil_temp - 1

		energy = transfer_medium.transferTo(soil, contactArea=surface_area, time=time)

		if verbose:
			print("energy transferred: {}/{}".format(abs(energy), energy_to_sink*time))
			print("medium temp after transfer: {}C".format(kelvin_to_c(transfer_medium.temperature)))

	print("----------------------")
	print("energy to transfer: {}W".format(round(energy_to_sink, 2)))
	print("energy transferred: {}W".format(round(abs(energy / time),2)))
	print("total time for complete cycle of medium: {}".format(round(time)))
	print("final length: {} meters".format(round(length,2)))
	print("energy transferred per meter: {}W/m".format(round(energy_to_sink / length,2)))



def main():
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--tube_diameter', help="diameter of tubing in meters", type=float, default=0.0127) # 1/2in ID
	parser.add_argument('--flow_rate', help="flow rate in liters per second", type=float, default=None) #3.5gpm = 0.22lps
	parser.add_argument('--max_tube_length', help="maximum length of tubing in meters", type=int, default=100000000000)
	parser.add_argument('--greenhouse', help="greenhouse characteristics file", type=str, default=None)
	parser.add_argument('--energy_input', help="energy to sink. if not specified, --greehouse will be used", type=int, default=None)
	parser.add_argument('--transfer_medium', help="air or water", type=str, default="water")
	parser.add_argument('--setpoint', help="desired temperature setpoint in C", default=32, type=int)
	parser.add_argument('--geothermal_temp', help="temperature  of geothermal mass in C", default=15, type=int)
	parser.add_argument('--verbose', help='verbose mode', action='store_true')

	args = parser.parse_args()

	greenhouse = {}

	if args.greenhouse:
		with open(args.greenhouse, "r") as configFile:
			greenhouse = json.loads(configFile.read())

	if not args.flow_rate and "pump_flow_rate" in greenhouse:
		args.flow_rate = greenhouse["pump_flow_rate"]

	if not args.flow_rate:
		raise Exception("error: must specify flow_rate argument or \"pump_flow_rate\" in greenhouse characteristics file (see --greenhouse)")


	startTemp = c_to_kelvin(args.setpoint)
	endTemp = c_to_kelvin(args.geothermal_temp)

	transfer_medium = Water(mass=1, temperature=startTemp)

	if args.transfer_medium == "air":
		transfer_medium = Air(mass=1, temperature=startTemp)


	if "greenhouse_dimensions" in greenhouse:
		greenhouse_dimensions = greenhouse["greenhouse_dimensions"]
		energy_to_sink=round(greenhouse_dimensions[0] * greenhouse_dimensions[1] * 1000, 2)


	# args.energy_input overrides greenhouse setting
	if args.energy_input:
		energy_to_sink = args.energy_input

	print("----------------------")
	print("Configuration: ")
	print("Tube diameter: {}m".format(args.tube_diameter))
	print("Energy to sink: {}W/m^-1)".format(energy_to_sink))
	print("Transfer medium: {}".format(args.transfer_medium))
	print("Setpoint: {}".format(args.setpoint))

	cooling_loop(transfer_medium, energy_to_sink, args.max_tube_length, args.tube_diameter, endTemp, args.flow_rate, verbose=args.verbose)

	#Use solar constant to figure out how much energy we need to sink:


if __name__ == "__main__":
	main()

