import click
from src.DataAnalysis import DataAnalysis
from src.UnitConversions import UnitConversions


@click.command()
@click.option(
    "-s",
    "--start-timestamp-us",
    default=0,
    type=int,
    help="Start timestamp in us for filtering data. Default is 0.",
)
@click.option(
    "-e",
    "--end-timestamp-us",
    default=2**32,
    type=int,
    help="End timestamp in us for filtering data. Default is 2^32.",
)
@click.argument("csv-file", type=click.Path(exists=True))
@click.option("-p", "--plot", is_flag=True, help="Plot current vs timestamp")
@click.option(
    "-d", "--dont-calculate", is_flag=True, help="Don't calculate average current"
)
@click.help_option("-h", "--help")
def main(
    start_timestamp_us: int,
    end_timestamp_us: int,
    csv_file: str,
    plot: bool,
    dont_calculate: bool,
):
    """Calculate average current consumption from a CSV file between start_timestamp_us and end_timestamp_us.
    If -p/--plot flag is used data will be plotted.

    Example usage:

    python analyse_data.py example.csv -s 3_000_000 -e 3_700_000 -p
    """

    da = DataAnalysis(csv_file, start_timestamp_us, end_timestamp_us)
    uc = UnitConversions()

    if not dont_calculate:
        print(
            f"Selected time window: {da.get_time_slice()} s ({uc.s_to_ms(da.get_time_slice())} ms)"
        )
        print(
            f"Number of values in selected time window: {da.get_number_of_used_values()}"
        )

        average_current_Ah = da.calculate_average_current()
        print(
            f"Average current consumption {average_current_Ah} Ah "
            f"({uc.A_to_mA(average_current_Ah)} mAh)"
        )

    if plot:
        # Plot current vs timestamp
        da.plot_current_vs_timestamp(
            "Timestamp (ms)",
            "Current (uA)",
            "Current vs Timestamp",
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting...")
        exit(0)
