library(arrow)

library(tidyverse)
library(sf)
library(svibuildr)
library(stringi)
library(readr)
library(glue)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


x = read.csv("C:/GitHub/paper_1/data/rs_means.csv")

model <- lm(log(x$cost) ~ log(x$sqft) + log(x$floors))
summary(model)

coefs <- coef(model)
x$estimate = exp(coefs[1]) * (x$sqft ** coefs[2]) * (x$floors ** coefs[3])
x
