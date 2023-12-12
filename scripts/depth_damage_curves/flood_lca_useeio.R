# Author: Sebastian Rowan
# Date: Fri Apr 14 13:38:07 2023
# Purpose: Calculate the economic demand induced by flood events as a result
#  of damages to residential structures.

library(tidyverse)
library(useeior)
library(readr)
library(readxl)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

model <- readRDS("USEEIOv2.0.1-411.rds")

data <- read_xlsx("../../data/House Plans/component_quantities_and_depth_damage.xlsx", sheet = "USEEIO Data")

codes <- data %>%
  filter(!is.na(naics_code)) %>%
  mutate(
    naics_code = paste0(naics_code, "/US"),
    unit_cost = as.numeric(unit_cost)
  )

demands <- codes$unit_cost
names(demands) <- codes$naics_code

x <- demands[1:3]
sapply(x, FUN = test, USE.NAMES = F)

codes2 <- cbind(codes, sapply(demands, FUN = run_lcia))
write.csv(codes, "useeio_results.csv")

run_lcia <- function(demand, code) {
  dv = demand
  names(dv) <- code

  # result_f <- calculateEEIOModel(
  #   model,
  #   perspective = "FINAL",
  #   demand = dv,
  #   use_domestic_requirements = FALSE
  # )
  
  # result_d <- calculateEEIOModel(
  #   model,
  #   perspective = "DIRECT",
  #   demand = dv,
  #   use_domestic_requirements = FALSE
  # )

  result_f_dom <- calculateEEIOModel(
    model,
    perspective = "FINAL",
    demand = dv,
    use_domestic_requirements = TRUE
  )
  
  # result_d_dom <- calculateEEIOModel(
  #   model,
  #   perspective = "DIRECT",
  #   demand = dv,
  #   use_domestic_requirements = TRUE
  # )
  

  # ghg_kg_d <- result_d$LCIA_d %>% as.data.frame() %>% select("Greenhouse Gases") %>% sum()
  # ghg_kg_d_dom <- result_d_dom$LCIA_d %>% as.data.frame() %>% select("Greenhouse Gases") %>% sum()
  # ghg_kg_f <- result_f$LCIA_f %>% as.data.frame() %>% select("Greenhouse Gases") %>% sum()
  ghg_kg_f_dom <- result_f_dom$LCIA_f %>% as.data.frame() %>% select("Greenhouse Gases") %>% sum()
  result <- result_f_dom$LCIA_f %>%
    as.data.frame() %>%
    summarize(across(
      c(
        "Greenhouse Gases", "Acidification Potential", "Eutrophication Potential","Freshwater Ecotoxicity Potential",
        "Human Health - Cancer", "Human Health - Noncancer", "Human Health Toxicity", "Human Health - Respiratory Effects",
        "Ozone Depletion", "Smog Formation Potential"
      ),
      ~(sum(.x, na.rm = T))
    ))

  # result <- c(ghg_kg_d, ghg_kg_d_dom, ghg_kg_f, ghg_kg_f_dom)

  return(result)
}

demands <- codes$unit_cost
names(demands) <- codes$naics_code

lcia <- imap(demands, run_lcia)
lcia <- do.call(rbind.data.frame, lcia)

codes2 <- cbind(codes, lcia)

write.csv(codes2, "useeio_results.csv")

x <- run_lcia(demands[1])
x
colnames(x)
as.matrix(x[1,])
