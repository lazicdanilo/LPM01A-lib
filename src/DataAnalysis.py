import matplotlib.pyplot as plt
import pandas as pd
from time import time
from src.UnitConversions import UnitConversions


class DataAnalysis:
    def __init__(
        self, filename: str, start_timestamp_us: int = 0, end_timestamp_us: int = 2**32
    ) -> None:
        """Initializes the DataAnalysis with the given filename and timestamps.

        Args:
            filename (str): The filename for the CSV file.
            start_timestamp_us (int, optional): The start timestamp in us for filtering data. Defaults to 0.
            end_timestamp_us (int, optional): The end timestamp in us for filtering data. Defaults to 2^32.
        """

        self.uc = UnitConversions()

        self.df = pd.read_csv(filename)

        self.filtered_df = self.df[
            (self.df["rx timestamp (us)"] >= start_timestamp_us)
            & (self.df["rx timestamp (us)"] <= end_timestamp_us)
        ]

    def calculate_average_current(self) -> float:
        """Calculates the average current consumption in Ah.

        Note:
            This function can take a while to run depending on the number of values.

        Returns:
            float: The average current consumption in Ah.
        """
        tick_start = time()
        mean_value_Ah = 0
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

            mean_value_Ah += mean_value_in_window_A * window_size_h

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

        return mean_value_Ah

    def get_number_of_used_values(self) -> int:
        """Returns the number of values within the given timestamps.

        Returns:
            int: The number of values within the given timestamps.
        """
        return len(self.filtered_df)

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
