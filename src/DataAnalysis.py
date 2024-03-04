import matplotlib.pyplot as plt
import pandas as pd
from time import time
import re
import shutil
from src.UnitConversions import UnitConversions


class CacheData:
    date: str
    time: str
    time_window_s: float
    time_window_ms: float
    num_values: int
    avg_current_Ah: float
    avg_current_mAh: float


class DataAnalysis:
    CACHED_DATA_NUMBER_OF_LINES = 13
    CACHED_DATA_PATTERN = (
        "##########################################################################################################"
        "# This comment is auto generated by data_analysis.py script from https://github.com/lazicdanilo/LPM01A-lib"
        "# It is used for caching the already calculated data. This comment should not be modified."
        "# If removed it will be re-created on next run of the script."
        "#"
        "# This will only be generated if the calculation is done for the"
        "# whole CSV file \(flags -s, --start and -e, --end are not used\)"
        "#"
        "# Generated on: (\d+-\d+-\d+)_(\d+:\d+:\d+)"
        "# Calculation time window: ([\d.]+(?:e[+-]?\d+)?) s \(([\d.]+(?:e[+-]?\d+)?) ms\)"
        "# Number of values: (\d+)"
        "# Average current consumption: ([\d.]+(?:e[+-]?\d+)?) Ah \(([\d.]+(?:e[+-]?\d+)?) mAh\)"
        "##########################################################################################################"
    )

    TEMP_FILE_PATH = "/tmp/temp.csv"

    def __init__(
        self,
        csv_file_path: str,
        start_timestamp_us: int = 0,
        end_timestamp_us: int = 2**64,
        try_cache: bool = True,
    ) -> None:
        """Initializes the DataAnalysis with the given csv_file_path and timestamps.

        Args:
            csv_file_path (str): The path of the CSV file.
            start_timestamp_us (int, optional): The start timestamp in us for filtering data. Defaults to 0.
            end_timestamp_us (int, optional): The end timestamp in us for filtering data. Defaults to 2^32.
            try_cache (bool, optional): Try to load the cached data from the CSV file. Defaults to True.
        """

        self.csv_file_path = csv_file_path

        self.uc = UnitConversions()

        self.cached_data = None
        if try_cache:
            self.cached_data = self._load_csv_cache(self.csv_file_path)

        self.df = pd.read_csv(self.csv_file_path, comment="#")

        self.filtered_df = self.df[
            (self.df["rx timestamp (us)"] >= start_timestamp_us)
            & (self.df["rx timestamp (us)"] <= end_timestamp_us)
        ]

    def _load_csv_cache(self, csv_file_path) -> CacheData:
        cd = CacheData()
        cached_data_str = ""
        try:
            with open(csv_file_path, "r") as file:
                for _ in range(self.CACHED_DATA_NUMBER_OF_LINES):
                    line = file.readline()
                    if not line:
                        return None
                    cached_data_str += line.strip()
        except FileNotFoundError:
            print(f"The file '{csv_file_path}' does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")

        if cached_data_str == "":
            return False

        match = re.search(self.CACHED_DATA_PATTERN, cached_data_str)

        if match:
            (
                cd.date,
                cd.time,
                cd.time_window_s,
                cd.time_window_ms,
                cd.num_values,
                cd.avg_current_Ah,
                cd.avg_current_mAh,
            ) = match.groups()

            cd.date = str(cd.date)
            cd.time = str(cd.time)
            cd.time_window_s = float(cd.time_window_s)
            cd.time_window_ms = float(cd.time_window_ms)
            cd.num_values = int(cd.num_values)
            cd.avg_current_Ah = float(cd.avg_current_Ah)
            cd.avg_current_mAh = float(cd.avg_current_mAh)

            return cd
        else:
            return None

    def get_csv_cache_data(self) -> CacheData:
        return self.cached_data

    def write_csv_cache_data(self, cached_data: CacheData) -> None:
        cache_data_str = (
            f"##########################################################################################################\n"
            f"# This comment is auto generated by data_analysis.py script from https://github.com/lazicdanilo/LPM01A-lib\n"
            f"# It is used for caching the already calculated data. This comment should not be modified.\n"
            f"# If removed it will be re-created on next run of the script.\n"
            f"#\n"
            f"# This will only be generated if the calculation is done for the\n"
            f"# whole CSV file (flags -s, --start and -e, --end are not used)\n"
            f"#\n"
            f"# Generated on: {cached_data.date}_{cached_data.time}\n"
            f"# Calculation time window: {cached_data.time_window_s} s ({cached_data.time_window_ms} ms)\n"
            f"# Number of values: {cached_data.num_values}\n"
            f"# Average current consumption: {cached_data.avg_current_Ah} Ah ({cached_data.avg_current_mAh} mAh)\n"
            f"##########################################################################################################\n"
        )

        # Open the existing file and the temporary file
        with open(self.csv_file_path, "r") as source_file, open(
            self.TEMP_FILE_PATH, "w"
        ) as temp_file:
            # Write the new data to the temporary file
            temp_file.write(cache_data_str)

            # Copy the existing content of the file to the temporary file
            shutil.copyfileobj(source_file, temp_file)
        # Replace the original file with the temporary file
        shutil.move(self.TEMP_FILE_PATH, self.csv_file_path)

    def calculate_average_current(self) -> float:
        """Calculates the average current consumption in Ah.

        Note:
            This function can take a while to run depending on the number of values.

        Returns:
            float: The average current consumption in Ah.
        """
        tick_start = time()
        mean_value_Ah = 0
        sum_value_Ah = 0
        percentage_done = 0
        eta = 0
        for i in range(len(self.filtered_df["rx timestamp (us)"])):
            if i == 0:
                continue

            window_size_us = (
                self.filtered_df["rx timestamp (us)"].iloc[i]
                - self.filtered_df["rx timestamp (us)"].iloc[i - 1]
            )

            mean_value_in_window_uA = (
                self.filtered_df["Current (uA)"].iloc[i - 1]
                + self.filtered_df["Current (uA)"].iloc[i]
            ) / 2

            mean_value_in_window_A = self.uc.uA_to_A(mean_value_in_window_uA)

            window_size_h = self.uc.us_to_h(window_size_us)

            sum_value_Ah += mean_value_in_window_A * window_size_h

            # Print percentage every 0.5 percent
            if (
                len(self.filtered_df["rx timestamp (us)"]) > 200
                and i % (len(self.filtered_df["rx timestamp (us)"]) // 200) == 0
            ):
                percentage_done += 0.5
                eta = (time() - tick_start) / percentage_done * (100 - percentage_done)
                print(
                    f"Progress: {percentage_done:.2f}%, ETA: {round(eta,2)}s",
                    end="\r",
                    flush=True,
                )
                if percentage_done == 100:
                    print(f"\nTime taken: {time() - tick_start:.2f} s")

        mean_value_Ah = sum_value_Ah / self.uc.s_to_h(self.get_time_slice())
        return mean_value_Ah

    def get_number_of_used_values(self) -> int:
        """Returns the number of values within the given timestamps.

        Returns:
            int: The number of values within the given timestamps.
        """
        return len(self.filtered_df)

    def get_time_slice(self) -> float:
        """Returns the time slice in seconds.

        Returns:
            float: The time slice in seconds.
        """
        return self.uc.us_to_s(
            self.filtered_df["rx timestamp (us)"].iloc[-1]
            - self.filtered_df["rx timestamp (us)"].iloc[0]
        )

    def plot_current_vs_timestamp(
        self, x_label: str = None, y_label: str = None, title: str = None
    ) -> None:
        """Plots the current vs timestamp.

        Args:
            x_label (str, optional): The x label. Defaults to None.
            y_label (str, optional): The y label. Defaults to None.
            title (str, optional): The title. Defaults to None.
        """

        plt.plot(
            self.filtered_df["rx timestamp (us)"], self.filtered_df["Current (uA)"]
        )

        if x_label:
            plt.xlabel(x_label)
        if y_label:
            plt.ylabel(y_label)
        if title:
            plt.title(title)

        plt.show()
