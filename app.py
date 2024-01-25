from pathlib import Path
from shiny import ui, render, reactive, App
import shinyswatch
import bayes_calculations as b

css_path = Path(__file__).parent / "www" / "calculator-theme.css"
currency = "€"
factor_projection = 1

"""
Main Shiny app for the Bayesian A/B-test Calculator
I have based the UI in the great AB test calculator developed by AB Testguide (https://abtestguide.com/bayesian/)
"""
app_ui = ui.page_fluid(
    #https://bootswatch.com/
    shinyswatch.theme.pulse(),
    ui.head_content(ui.HTML("""
      <!-- Google tag (gtag.js) -->
      <script async src="https://www.googletagmanager.com/gtag/js?id=G-EE3R9DZV33"></script>
      <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-EE3R9DZV33');
      </script>""")),
    ui.include_css(css_path),
    ui.output_ui("head_html"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.tags.div(
              ui.tags.div(ui.input_numeric("visitors_A", "Users A", value=5000), class_="form-group col-md-6 col-xs-12"),
              ui.tags.div(ui.input_numeric("conversions_A", "Conversions A", value=1500), class_="form-group col-md-6 col-xs-12"),
              class_="row"
            ),
            ui.tags.div(
              ui.tags.div(ui.input_numeric("visitors_B", "Users B", value=5000), class_="form-group col-md-6 col-xs-12"),
              ui.tags.div(ui.input_numeric("conversions_B", "Conversions B", value=1600), class_="form-group col-md-6 col-xs-12"),
              class_="row"
            ),
            ui.input_numeric("test_duration", "Test duration in days", value=14),
            ui.input_slider("percent_traffic_in_test", "Percentage of traffic", 1, 100, 100),
            ui.tags.div(
              ui.tags.div(ui.input_numeric("aov", "AOV", value=100), class_="form-group col-md-6 col-xs-12"),
              ui.tags.div(ui.input_numeric("min_rev_yield", "Min revenue yield", value=1000), class_="form-group col-md-6 col-xs-12"),
              class_="row"
            ),
            ui.tags.div(
              ui.tags.div(ui.input_switch("currency_switch", "$/€", True), class_="form-group col-md-4 col-xs-12"),
              ui.tags.div(ui.input_switch("year_assessment_switch", "6/12 months projection", True), class_="form-group col-md-8 col-xs-12"),
              class_="row"
            ),
            
            ui.input_action_button("compute", "Calculate", class_="btn-primary")
        ),
        ui.panel_main(
            ui.output_ui("main_result"),           
            ui.output_ui("risk_assesment"),
            ui.output_ui("posterior_simulation"),
            ui.output_ui("posterior_simulation_diff"),
        ),
    ),
)

def server(input, output, session):
    """
    This function defines the shiny server that takes input, output, and session as parameters.
    It initializes a bayesCalculations object and defines several reactive event functions for different UI outputs and plots.
    """

    calc = b.bayesCalculations()
    
    @reactive.Effect
    @reactive.event(input.compute)
    def _():
        """
        A "side effect" function that is called when the "Calculate" button is clicked. 
        It calculates probabilities using Bayesian inference and handles ValueError exceptions.
        """
        global currency
        global factor_projection

        if input.currency_switch():
            currency = "€"
        else:
            currency = "$"

        if input.year_assessment_switch():
            factor_projection = 2
        else:
            factor_projection = 1

        try:
          #b = bayesCalculations(visitors_A, conversions_A, visitors_B, conversions_B, test_duration, traffic_test, aov, min_rev_yield)
          calc.setValues(input.visitors_A(), input.conversions_A(), input.visitors_B(), input.conversions_B(), input.test_duration(), input.percent_traffic_in_test(), input.aov(), input.min_rev_yield())
          calc.generate_posterior_samples()
          calc.calculate_probabilities()

        except ValueError:
            m = ui.modal(
            "An error occured, please check the test data input and try again.",
            title="",
            easy_close=True,
            footer=None)
            ui.modal_show(m)

    @output
    @render.ui
    def head_html():
        """
        A function that generates the HTML for the header of the Bayesian A/B-test Calculator app.
        """
        head_html_info = """
        <header>
        <div class="row">
          <div class="col-md-12">
            <h1 id="title">Bayesian A/B-test Calculator</h1> 
            <h2 class="header">This app is based on a <a href="https://abtestguide.com/bayesian/" target="_blank">Bayesian A/B-test Calculator</a> by AB Testguide. 
            The calculations are implemented with Python and the interface and deployment with Shiny for Python.  Developed by <a href="https://www.linkedin.com/in/fernandomaquedano/" target="_blank">Fer Maquedano</a>.
            </h2>
          </div>
        </div>
        </header>"""
        return ui.HTML(head_html_info)

    @output
    @render.ui
    @reactive.event(input.compute)
    def main_result():
        """
        A function to generate the main test result UI, including probability charts and table data.
        """
        main_result_info = """
        <div class="block">
            <h3>Main test result</h3>
            <h4>Probability of each variant being the best experience</h4>
            <div id="outperforming-chart" class="ct-outperforming">""" + str(ui.output_plot("plot_1")) + """</div>
            <table class="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th class="align-right">Users</th>
                  <th class="align-right">Conversion</th>
                  <th class="align-right">CR</th>
                  <th class="align-right">Uplift</th>
                  <th class="align-right move-tds">Chance of being best</th>
                <th class="align-right move-tds">Chance of at least """ + currency + f"{input.min_rev_yield():,}" + """ extra revenue</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>A</td>
                  <td class="align-right">""" + f"{input.visitors_A():,}" + """</td>
                  <td class="align-right">""" + f"{input.conversions_A():,}" + """</td>
                  <td class="align-right">""" + f"{calc.control_cr:.1%}" + """</td>
                  <td></td>
                  <td></td>
                  <td></td>
                </tr>
                <tr>
                  <td>B</td>
                  <td class="align-right">""" + f"{input.visitors_B():,}" + """</td>
                  <td class="align-right">""" + f"{input.conversions_B():,}" + """</td>
                  <td class="align-right">""" + f"{calc.variant_cr:.1%}" + """</td>
                  <td class="align-right">""" + f"{calc.relative_difference:.2%}" + """</td>
                  <td class="align-right move-tds">""" + f"{calc.prob_B:.1%}" + """</td>
                  <td class="align-right move-tds">""" + f"{calc.prob_yield_mean:.1%}" + """</td>
                </tr>
              </tbody>
            </table>
            <p class="table-caption">Based on """ + f"{input.test_duration()}" + """ days of data, on average """ + f"{(input.visitors_A()+input.visitors_B())/2:,.0f}" + """ users per variation</p>
        </div>"""
        
        return ui.HTML(main_result_info)
        
    @output
    @render.ui
    @reactive.event(input.compute)
    def risk_assesment():
        """
        This function generates a risk assessment report with probability and effect on revenue for implementing B. 
        It returns the risk assessment report as an HTML object.
        """
        risk_assesment_info = """<div class="block">
              <h3>Risk assessment of implementing B</h3>
            <div class="row">
              <div class="col-md-8">
                <table class="table">
                  <thead>
                    <tr>
                      <th>Implement B</th>
                      <th class="align-right">Probability</th>
                      <th class="align-right">Effect on revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Expected risk</td>
                      <td class="align-right">""" + f"{calc.prob_A:.1%}" + """</td>
                      <td class="align-right">""" + currency + f"{abs(calc.expected_risk) * factor_projection:,.0f}" + """</td>
                    </tr>
                    <tr>
                      <td>Expected uplift</td>
                      <td class="align-right">""" + f"{calc.prob_B:.1%}" + """</td>
                      <td class="align-right">""" + currency + f"{calc.expected_uplift * factor_projection:,.0f}" + """</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="col-md-4">
                <div class="contribution """ + "%s" %("negative-contribution" if calc.total_contribution < 0  else "") + """">
                  <div class="contribution-label">Total contribution</div>
                  <div class="contribution-amount">
                    """ + currency + f"{abs(calc.total_contribution) * factor_projection:,.0f}" + """
                  </div>
                </div>
              </div>
              </div>
              <div class="row">
              <div class="col-md-12">
            <p class="table-caption">Based on an average order value of """ + currency + f"{input.aov():,}" + """ and """ + f"{6 * factor_projection}" + """ months time</p>
            </div>
              </div>
            </div>"""
        return ui.HTML(risk_assesment_info)

    @output
    @render.ui
    @reactive.event(input.compute)
    def posterior_simulation():
        """
        A function that performs a posterior simulation. It returns an HTML object containing information about the posterior simulation of A and B distributions.
        """
        posterior_simulation_info = """
        <div class="block">
            <h3>Posterior simulation of A and B distributions</h3>
            <h4>Monte Carlo simulation of Beta(1,1) of a Bernoulli distribution with 500,000 random trials. 
            Shows the conversion rates of both A and B simulations (x axis) and its frequency percentage out of total samples (y axis)</h4>
            <div id="test-results-chart" class="">""" + str(ui.output_plot("plot_2")) + """</div>
        </div>"""
        return ui.HTML(posterior_simulation_info)
    
    @output
    @render.ui
    @reactive.event(input.compute)
    def posterior_simulation_diff():
        """
        Html section for posterior simulation of differences between A and B: (B/A -1 * 100)% as a relative change
        """
        posterior_simulation_diff_info = """
        <div class="block">
            <h3>Posterior simulation of difference</h3>
            <h4>Difference in conversion rate between B and A. Shows the relative conversion rate increase
            (x axis) and its frequency percentage out of total samples (y axis)</h4>
            <div id="test-results-chart" class="">""" + str(ui.output_plot("plot_3")) + """</div>
        </div>"""
        return ui.HTML(posterior_simulation_diff_info)   
        
    @output
    @render.plot
    @reactive.event(input.compute)
    def plot_1():
        return calc.plot_bayesian_probabilities()
        
    @output
    @render.plot
    @reactive.event(input.compute)
    def plot_2():
        return calc.plot_simulation()
    
    @output
    @render.plot
    @reactive.event(input.compute)
    def plot_3():
        return calc.plot_simulation_of_difference()


app = App(app_ui, server, debug=False)


