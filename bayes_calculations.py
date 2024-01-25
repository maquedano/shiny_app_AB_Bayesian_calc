import matplotlib.pyplot as plt
import scipy.stats as scs
import matplotlib.ticker as mtick
import seaborn as sns
from matplotlib.ticker import AutoMinorLocator

roboto = {"fontname": "system-ui", "size": "12"}
NUM_POSTERIOR_SAMPLES = 500000


"""
Class where all the calculations are encapulated. Bayesian calculations are based on the calculator 
developed by rjjfox (https://github.com/rjjfox/ab-test-calculator) for a streamlit application
"""
class bayesCalculations(object):
    def __init__(self):
        return
        
    def setValues(self, visitors_A, conversions_A, visitors_B, conversions_B, test_duration, percent_traffic_in_test, aov, min_rev_yield):
        self.visitors_A = visitors_A
        self.conversions_A = conversions_A
        self.visitors_B = visitors_B
        self.conversions_B = conversions_B
        self.control_cr = conversions_A / visitors_A
        self.variant_cr = conversions_B / visitors_B
        self.relative_difference = self.variant_cr / self.control_cr - 1
        self.test_duration = test_duration
        self.percent_traffic_in_test = percent_traffic_in_test
        self.min_rev_yield = min_rev_yield
        self.aov = aov 
        
    def generate_posterior_samples(self):
        """Generates samples for the posterior distributions of A and B."""
        # Set alpha and beta priors
        alpha_prior = 1
        beta_prior = 1

        # Calculate posterior distribution for A
        posterior_A = scs.beta(alpha_prior + self.conversions_A,
                            beta_prior + self.visitors_A - self.conversions_A)

        # Calculate posterior distribution for B
        posterior_B = scs.beta(alpha_prior + self.conversions_B,
                            beta_prior + self.visitors_B - self.conversions_B)

        # Generate posterior simulation samples
        self.samples_posterior_A = posterior_A.rvs(NUM_POSTERIOR_SAMPLES)
        self.samples_posterior_B = posterior_B.rvs(NUM_POSTERIOR_SAMPLES)
        
    def calculate_probabilities(self):
        """Calculate the likelihood that the variants are better"""
        
        # Calculate the probabilities
        self.prob_A = (self.samples_posterior_A > self.samples_posterior_B).mean()
        self.prob_B = (self.samples_posterior_A <= self.samples_posterior_B).mean()
        
        # Calculate the difference in posterior samples between variant B and variant A, filter between positive and negative
        difference = self.samples_posterior_B / self.samples_posterior_A - 1
        self.greater = difference[difference > 0]
        self.lower = difference[difference < 0]
        # Calculate means for positive and negative relative changes
        mean_positive_difference = 0 if self.greater.size == 0 else self.greater.mean()
        mean_negative_difference = 0 if self.lower.size == 0 else self.lower.mean()

        # Calculate the number of visitors and revenue in six months
        six_months_in_days = 182.5
        visitors_in_six_months = (self.visitors_A + self.visitors_B) / (self.percent_traffic_in_test / 100) / self.test_duration * six_months_in_days
        revenue_in_six_months = visitors_in_six_months * self.control_cr * self.aov 
        
        # Calculate the expected risk and expected uplift
        self.expected_risk = revenue_in_six_months * mean_negative_difference
        self.expected_uplift = revenue_in_six_months * mean_positive_difference
        
        # Calculate the minimum uplift probability
        min_uplift_prob = self.min_rev_yield / revenue_in_six_months 
        
        # Calculate the probability of achieving the minimum uplift
        self.prob_yield_mean = (difference >= min_uplift_prob).mean()
        
        # Calculate the total contribution
        self.total_contribution = self.expected_risk * self.prob_A + self.expected_uplift * self.prob_B

    def plot_bayesian_probabilities(self, labels=["A", "B"]):
        """
        Plots a horizontal bar chart of the likelihood of either variant being
        the winner
        """

        fig, ax = plt.subplots(figsize=(10, 4), dpi=75)
        ax.patch.set_alpha(0.8)
        
        snsplot = ax.barh(
            labels[::-1], [self.prob_B, self.prob_A], color=["#51c4a8", "#da6d75"]
        )

        # Display the probabilities by the bars
        # Parameters for ax.text based on relative bar sizes
        if self.prob_A < 0.2:
            A_xpos = self.prob_A + 0.01
            A_alignment = "left"
            A_color = "black"
            B_xpos = self.prob_B - 0.01
            B_alignment = "right"
            B_color = "white"
        elif self.prob_B < 0.2:
            A_xpos = self.prob_A - 0.01
            A_alignment = "right"
            A_color = "white"
            B_xpos = self.prob_B + 0.01
            B_alignment = "left"
            B_color = "black"
        else:
            A_xpos = self.prob_A - 0.01
            A_alignment = "right"
            A_color = "white"
            B_xpos = self.prob_B - 0.01
            B_alignment = "right"
            B_color = "white"

        # Plot labels using previous parameters
        ax.text(
            A_xpos,
            snsplot.patches[1].get_y() + snsplot.patches[1].get_height() / 2.1,
            f"{self.prob_A:.1%}",
            horizontalalignment=A_alignment,
            color=A_color,
            **roboto,
        )
        ax.text(
            B_xpos,
            snsplot.patches[0].get_y() + snsplot.patches[0].get_height() / 2.1,
            f"{self.prob_B:.1%}",
            horizontalalignment=B_alignment,
            color=B_color,
            **roboto,
        )

        ax.xaxis.grid(color="lightgrey")
        ax.tick_params(axis='x', colors='#595959')
        ax.set_axisbelow(True)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        sns.despine(left=True, bottom=True)
        ax.tick_params(axis="both", which="both", bottom=False, left=False)
        fig.tight_layout()
        return fig

    def plot_simulation(self):
        """
        Plots a histogram showing the distribution of A and B
        highlighting the difference between them
        """

        fig, ax = plt.subplots(figsize=(10, 4), dpi=75)
        ax.patch.set_alpha(0.8)

        sns.histplot(self.samples_posterior_A, bins=50, color="#da6d75", shrink=0.75, edgecolor="black", linewidth=0.1)
        sns.histplot(self.samples_posterior_B, bins=50, color="#51c4a8", shrink=0.75, edgecolor="black", linewidth=0.1)

        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: format(x / len(self.samples_posterior_A), ".0%"))
        )

        plt.legend(labels=["distribution A", "distribution B"], loc = "lower center", bbox_to_anchor=(0.5, -0.4), ncol=2, frameon=False, handleheight=1.25, handlelength=1)

        # Set grid lines as grey and display behind the plot
        ax.yaxis.grid(color="lightgrey")
        ax.set_axisbelow(True)

        # Remove y axis line and label and dim the tick labels
        sns.despine(left=True)
        ax.set_ylabel("")
        ax.tick_params(axis="y", colors="lightgrey")
        ax.tick_params(axis='x', colors='#595959')
        ax.tick_params(axis='x', which='minor', colors='#595959', pad=4.9)
    
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.xaxis.set_minor_formatter(mtick.PercentFormatter(1))
        fig.tight_layout()

    def plot_simulation_of_difference(self):
        """
        Plots a histogram showing the distribution of the differences between
        A and B highlighting how much of the difference shows a positve diff
        vs a negative one.
        """

        fig, ax = plt.subplots(figsize=(10, 4), dpi=75)
        ax.patch.set_alpha(0.8)

        difference = self.samples_posterior_B / self.samples_posterior_A - 1

        greater = difference[difference > 0]
        lower = difference[difference < 0]

        sns.histplot(greater, binwidth=0.005, color="#51c4a8", shrink=0.75, edgecolor="black", linewidth=0.1)

        if lower.size != 0:
            lower_limit = round(lower.min(), 2)
            sns.histplot(
                lower, binwidth=0.005, binrange=(lower_limit, 0), color="#da6d75", shrink=0.75, edgecolor="black", linewidth=0.1
            )

        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: format(x / len(difference), ".0%"))
        )

        # Set grid lines as grey and display behind the plot
        ax.yaxis.grid(color="lightgrey")
        ax.set_axisbelow(True)

        # Remove y axis line and label and dim the tick labels
        sns.despine(left=True)
        ax.set_ylabel("")
        ax.tick_params(axis="y", colors="lightgrey")
        ax.tick_params(axis='x', colors='#595959')
        ax.tick_params(axis='x', which='minor', colors='#595959', pad=4.9)
    
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.xaxis.set_minor_formatter(mtick.PercentFormatter(1))
        fig.tight_layout()

