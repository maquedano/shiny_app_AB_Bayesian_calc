# Bayesian A/B-test Calculator

Trying to understand the underlying statistics, I developed a Bayesian A/B test calculator based upon an existing calculator that I use by AB Testguide as a UI reference; 
and based on the calculator developed by rjjfox (https://github.com/rjjfox/ab-test-calculator) for a streamlist application. But in this case I port the calculator into
the [Shiny for python ](https://shiny.posit.co/py/) ecosystem.

* APP deployed on → https://maquedano.shinyapps.io/bayesian-ab-test-calc/

### For deploying the Shiny app
* For deploying the app I followed the [deployment instructions](https://shiny.posit.co/py/docs/deploy-cloud.html)  on their web. 
* Basically create an account on [shinyapps.io](https://www.shinyapps.io/), which offers hosting up to 5 apps per user for free
* Get your token from the account (Account > Tokens > Add Token > Show > With Python > Copy to clipboard)
* run in your app folder the followig command in a terminal to initialize the connections and credentials with shinyapps.io 
`rsconnect add --account maquedano --name maquedano --token XXXXXXXXXX`
* Deploy the app with the following command
`rsconnect deploy shiny . --name maquedano --title bayesian-AB-test-calc`
