

library(ggplot2)
library(ggpmisc)
library(kableExtra)
library(gt)
library(gtsummary)
library(dplyr)
library(arrow)
library(sf)
library(EnvStats)
library(knitr)
library(latex2exp)
library(ggthemes)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


plans <- readxl::read_xlsx("../data/component_quantities_and_depth_damage.xlsx", sheet = "floor_plans")
x <- read_parquet("../data/fragility_table.parquet")
components <- read_parquet("../data/fragility_table.parquet") %>%
  filter(
    flood_depth %in% c(-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30),
    run == 0
  )  %>%
  select(
    component = component_x,
    unit,
    cost_mean = total_cost_mean,
    cost_sd = total_cost_sd,
    co2_mean = unit_co2_mean,
    co2_sd = unit_co2_sd,
    flood_depth,
    fragility
  ) %>%
  mutate(
    flood_depth = paste0('d',flood_depth)
  ) %>%
  group_by(component) %>%
  tidyr::pivot_wider(
    names_from = flood_depth,
    values_from = fragility
  )

dd_curves_usace <- read_parquet("../data/g2crm_dmg_fns.parquet")
dd_curves_usace$source <- "G2CRM"
rows_to_add <- tail(dd_curves_usace[dd_curves_usace$flood_depth == 24,], 2) %>% mutate(flood_depth = 31.9)
dd_curves_usace <- rbind(dd_curves_usace, rows_to_add)

dd_curves_gec <- read_parquet("../data/gec_dmg_fns.parquet")

dd_curves_gcs <- read_parquet("../data/gcs_dmg_fns.parquet")
dd_curves_gcs2 <- read_parquet("../data/gcs_dmg_fns2.parquet")
dd_curves_study <- read_parquet("../data/study_dmg_fns.parquet")



dd_curves <- plyr::rbind.fill(dd_curves_study, dd_curves_gec) %>%
  filter(flood_depth >= -4)

dd_curves$dmg_low_fix <- dd_curves$dmg_low * (dd_curves$dmg_low > 0)

mcs_results = read_parquet("../data/mcs_results.parquet")
streams = st_read("../data/all_streams.geojson", quiet = TRUE)
svi_all <- readRDS("../data/svi_all.rds") %>%
  st_drop_geometry()

tract_results <- read_parquet("../data/tract_results.parquet")
tract_results <- st_as_sf(tract_results) %>%
  st_set_crs(st_crs(streams)) %>%
  left_join(
    svi_all,
    by = c("GEOID" = "GEOID")
  )


region_results <- read_parquet("../data/region_results.parquet")


### Triang CDF --------
a <- 0
b <- 1
c <- 0.6

x <- seq(0, 1, 0.05)
xlabs <- c('a', 'c', 'b')
ybreaks <- ptri(q=c(a,c,b), min=a, max=b, mode=c)
ylabs <- c('0.0', TeX("$\\frac{c-a}{b-a}$"), '1.0')
y = ptri(q = x, min=a, max=b, mode=c)

ggplot() +
  geom_line(aes(x=x, y=y)) +
  # c vertical line
  geom_segment(aes(
    x=c, y=0,
    xend=c, yend=ybreaks[2]
    ),
    linetype='dashed', lwd=0.2
  ) +
  # c horizontal line
  geom_segment(aes(
    x=0, y=ybreaks[2],
    xend=ybreaks[2], yend=ybreaks[2]
  ),
  linetype='dashed', lwd=0.2
  ) +
  # b vertical line
  geom_segment(aes(
    x=1, y=0,
    xend=1, yend=1
  ),
  linetype='dashed', lwd=0.2
  ) +
  # b horizontal line
  geom_segment(aes(
    x=0, y=1,
    xend=1, yend=1
  ),
  linetype='dashed', lwd=0.2
  ) +
  scale_x_continuous(
    name="",
    breaks=c(a, c, b),
    labels = xlabs
  ) +
  scale_y_continuous(
    name="",
    breaks=ybreaks,
    labels = ylabs
  ) +
  theme_few()


### Study regions map --------

#TODO: add region labels

ggplot() +
  geom_sf(
    tract_results,
    mapping = aes(geometry = geometry)
  ) +
  geom_sf(
    streams,
    mapping = aes(geometry = geometry),
    color = "blue"
  ) 


### Damge curve compare -------


dd_curves <- dd_curves %>%
  mutate(
    occdesc = if_else(
      occtype == "RES1-1S",
      "One Story",
      "Two Story"
    )
  )

ggplot(dd_curves) +
  geom_ribbon(
    aes(
      x = flood_depth,
      ymin = dmg_low_fix,
      ymax = dmg_high,
      fill = source
    ),
    alpha = 0.4
  ) +
  geom_line(
    aes(
      x = flood_depth,
      y = dmg_mean,
      color = source
    ),
    lwd = 1.5
  ) +
  scale_y_continuous(labels = scales::percent) +
  labs(
    # title = "Depth-Damage Curves for Single-Family Residential Structures",
    x = "Flood Depth (ft)",
    y = "Damage Cost (% Structure Value)"
  ) +
  theme(
    legend.position = 'bottom'
  ) +
  facet_wrap(~ occdesc)

### Study damage functions --------

#TODO: use cowplot to combine these two plots

p1 <- ggplot(dd_curves_study) +
  geom_ribbon(
    aes(
      x = flood_depth,
      ymin = co2_low,
      ymax = co2_high
    ),
    alpha = 0.4
  ) +
  geom_line(
    aes(
      x = flood_depth,
      y = co2_mean
    ),
    lwd = 1.5
  ) +
  labs(
    # title = "Depth-Emissions Curves for Single-Family Residential Structures",
    x = "Flood Depth (ft)",
    y = "GHG Emissions (kg CO2eq)"
  ) +
  facet_wrap(~ occtype)

p2 <- dd_curves_study %>%
  mutate(
    co2_cost_pct_low = if_else(
      co2_cost_pct_low < 0,
      0,
      co2_cost_pct_low
    )
  ) %>%
  ggplot() +
  geom_ribbon(
    aes(
      x = flood_depth,
      ymin = co2_cost_pct_low,
      ymax = co2_cost_pct_high
    ),
    alpha = 0.4
  ) +
  geom_line(
    aes(
      x = flood_depth,
      y = co2_cost_pct_mean
    ),
    lwd = 1.5
  ) +
  scale_y_continuous(labels = scales::percent) +
  labs(
    x = "Flood Depth (ft)",
    y = "Social Cost of GHG Emissions (% Structure Value)"
  ) +
  facet_wrap(~ occtype)

### Regression --------

#TODO: add results table to figure

p3 <- ggplot(mcs_results, aes(
      x = sum_damage_triang,
      y = sum_co2_triang
      # x = co2_cost_pct,
      # y = damage_pct_rs
    )) +
  geom_point(
    alpha = 0.4,
    shape = '.',
    size = 2
  ) +
  labs(
    x = "Damage Cost",
    y = "GHG Emissions (kg CO2eq)"
  ) +
  scale_x_continuous(labels = scales::dollar_format()) +
  stat_poly_line() +
  stat_poly_eq()


mcs_results <- mcs_results %>%
  mutate(damage_cost = sum_damage_triang)

model = lm(
  formula = sum_co2_triang ~ damage_cost,
  data = mcs_results
)

model_pct = lm(
  formula = co2_cost_pct ~ damage_pct_rs,
  data = mcs_results
)

t1 <- model %>%
  tbl_regression(
    intercept = TRUE,
    conf.int = FALSE
  ) %>%
  modify_header(
    label = "**Coefficient**",
    estimate = "**Estimate**"
  ) %>%
  add_glance_table(include = c(r.squared)) %>%
  as_gt() %>%
  as_latex()


### Region-tract results --------

tract_results %>%
  mutate(
    pct_change_mean = pct_change_mean - 1
  ) %>%
  ggplot() +
    geom_sf(aes(fill = pct_change_mean), color = NA) +
    scale_fill_distiller(
      name = "Percent Change",
      labels = scales::percent,
      palette = "YlOrRd",
      direction = 1
    )

### SVI Results --------

tract_results %>%
  mutate(
    region = gsub(
      "burlington_davenport",
      "Burlington-Davenport",
      gsub(
        "paducah_cairo",
        "Paducah-Cairo",
        region.x
      )
    )
  ) %>%
  filter(!is.na(pct_change_mean)) %>%
  ggplot(aes(x = rpl_themes, y = pct_change_mean - 1)) +
  geom_point() +
  stat_poly_line() +
  stat_poly_eq() +
  labs(
    x = "Social Vulnerability Index",
    y = "Cost Increase From GHG"
  ) +
  scale_y_continuous(labels = scales::percent) +
  facet_wrap(~ region, nrow = 2)

# is this needed???
x <- tract_results %>%
  mutate(
    region = gsub(
      "burlington_davenport",
      "Burlington-Davenport",
      gsub(
        "paducah_cairo",
        "Paducah-Cairo",
        region.x
      )
    ),
    pct_change_mean = pct_change_mean - 1
  ) %>%
  filter(!is.na(pct_change_mean)) %>%
  group_by(region) %>%
  summarize(
    min_pct = min(pct_change_mean) * 100,
    max_pct = max(pct_change_mean) * 100
  ) %>% st_drop_geometry()