library(ggplot2)
library(ggpmisc)
library(gt)
library(gtsummary)
library(dplyr)
library(arrow)
library(sf)
library(EnvStats)
library(knitr)
library(latex2exp)
library(ggthemes)
library(cowplot)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
theme_paper <- function(){
  theme_few() %+replace%
    theme(
      axis.text = element_text(size = 16),
      axis.title = element_text(face = 'bold', size = 20),
      strip.text = element_text(face = 'bold', size = 20),
      legend.text = element_text(size = 14),
      legend.title = element_text(size = 14),
      plot.title = element_text(face = 'bold', size = 20)
    )
}

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
dd_curves_study <- read_parquet("../data/study_dmg_fns.parquet") %>%
  mutate(source = "Monte Carlo Analysis")



dd_curves <- plyr::rbind.fill(dd_curves_study, dd_curves_gec, dd_curves_gcs, dd_curves_gcs2) %>%
  filter(flood_depth >= -4)

dd_curves$dmg_low_fix <- dd_curves$dmg_low * (dd_curves$dmg_low > 0)

mcs_results = read_parquet("../data/mcs_results.parquet")

streams = st_read("../data/region_streams.geojson", quiet = TRUE)
bd_streams = st_read("../data/bd_streams.geojson", quiet = TRUE)
pc_streams = st_read("../data/pc_streams.geojson", quiet = TRUE)


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



### ----

### Triang CDF --------
a <- 0
b <- 1
c <- 0.6

x <- seq(0, 1, 0.05)
xlabs <- c('a', 'c', 'b')
ybreaks <- ptri(q=c(a,c,b), min=a, max=b, mode=c)
ylabs <- c('0.0', TeX("$\\frac{c-a}{b-a}$"), '1.0')
y = ptri(q = x, min=a, max=b, mode=c)

dashed_lwd = 1
main_lwd = 3

triangcdf <- ggplot() +
  geom_line(
    aes(x=x, y=y),
    lwd = main_lwd,
    lineend = "round"
  ) +
  # c vertical line
  geom_segment(aes(
    x=c, y=0,
    xend=c, yend=ybreaks[2]
    ),
    linetype='dashed', lwd=dashed_lwd
  ) +
  # c horizontal line
  geom_segment(aes(
    x=0, y=ybreaks[2],
    xend=ybreaks[2], yend=ybreaks[2]
  ),
  linetype='dashed', lwd=dashed_lwd
  ) +
  # b vertical line
  geom_segment(aes(
    x=1, y=0,
    xend=1, yend=1
  ),
  linetype='dashed', lwd=dashed_lwd
  ) +
  # b horizontal line
  geom_segment(aes(
    x=0, y=1,
    xend=1, yend=1
  ),
  linetype='dashed', lwd=dashed_lwd
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
  theme_paper()

eqn <- "P[Failure|Depth = x] = {\begin{cases}  0 & {\text{for }} x\leq a\\  {\frac {(x-a)^{2}}{(b-a)(c-a)}} & {\text{for }} a<x\leq c\\  1-{\frac {(b-x)^{2}}{(b-a)(b-c)}} & {\text{for }} c<x<b\\  1 & {\text{for }} b\leq x\end{cases}}"

eqcdf <- ggdraw() + draw_image(magick::image_read_svg("figures/eq-triangcdf.svg"))

### table --------
components2 <- read_parquet("../data/components.parquet") %>%
  rename(component = component_x) %>%
  select(
    component, unit,  min, mode, max, unit_cost_min, unit_cost_mean, unit_cost_max,
    unit_co2_min, unit_co2_mean, unit_co2_max
  )

roof <- components2[substr(components2$component, 1, 10) == "Roof Cover",] %>%
  mutate(
    component = "Roof Cover"
  ) %>%
  group_by(component, unit) %>%
  summarize(
    unit_cost_mean = sum(unit_cost_mean),
    unit_cost_min = sum(unit_cost_min),
    unit_cost_max = sum(unit_cost_max),
    unit_co2_mean = sum(unit_co2_mean),
    unit_co2_min = sum(unit_co2_min),
    unit_co2_max = sum(unit_co2_max),
    min = 8,
    max = 8.01,
    mode = 8
  ) %>%
  select(
    component, unit,  min, mode, max, unit_cost_min, unit_cost_mean, unit_cost_max,
    unit_co2_min, unit_co2_mean, unit_co2_max
  )

components3 <- components2[substr(components2$component, 1, 10) != "Roof Cover",]

components2 <- rbind(components3, roof)

nist_rows <- c(
  "Underfloor Insulation", "Wood Subfloor", "Finished Floor Underlayment", "Finished Floor", "Wall Paint - Interior", "Wall Paint - Exterior", "Sheetrock/drywall", "Wall Insulation", "Baseboard", "Ceiling", "Ceiling Paint", "Ceiling Insulation", 
  "Roof Cover", "Roof Sheathing", "Facade", "Exterior Wall Sheathing"
)
nist_rows <- c(nist_rows, paste("2nd Floor", nist_rows))

ecoinvent_rows <- c(
  "Underfloor Insulation", "Underfloor Ductwork", "Heating/Cooling Unit or HVAC", "Wood Subfloor", "Finished Floor Underlayment", "Bottom Cabinets", "Top Cabinets", "Bathroom Bottom Cabinets", "Bathroom Top Cabinets", "Exterior Doors", "Interior Doors", "Baseboard", "Refrigerator", "Dishwasher", "Microwave", "Clothes Washer", "Clothes Dryer", "Oven/stove", "Range hood", "Bottom Outlets", "Top Outlets", "Light Switches", "Wiring", "Windows"
)
ecoinvent_rows <- c(ecoinvent_rows, paste("2nd Floor", ecoinvent_rows))

component_names <- components2$component
nist_index <- match(nist_rows, component_names)
nist_index <- nist_index[!is.na(nist_index)]

ecoinvent_index <- match(ecoinvent_rows, component_names)
ecoinvent_index <- ecoinvent_index[!is.na(ecoinvent_index)]

raluy_index <- match("Water Heater", component_names)
adhikari_silva_index <- match("Counter Tops", component_names)
useeio_index <- match("Electrical Panel", component_names)

components2[,c('ref1', 'ref2', 'ref3', 'ref4', 'ref5')] <- ""
components2[nist_index, "ref1"] <- "NIST, 2023"
components2[ecoinvent_index, "ref2"] <- "ecoinvent, 2023"
components2[raluy_index, "ref3"] <- "Raluy and Dias, 2020"
components2[adhikari_silva_index, "ref4"] <- "Adhikari et al., 2022; Silva et al., 2021"
components2[useeio_index, "ref5"] <- "Ingwersen et al., 2022"

components2$co2_ref <- paste0("(",paste(components2$ref1, components2$ref2, components2$ref3, components2$ref4, components2$ref5, sep="; "),")")
components2$co2_ref <- gsub("; \\)", "\\)",gsub("\\(; ", "\\(", gsub("; ;", ";", gsub("; ;", ";", components2$co2_ref))))


# TODO: change footnotes for GHG sources to component name and add text saying "GHG Emissions source:"

components2 %>%
  select(
    component, unit,  min, max, mode, unit_cost_min, unit_cost_max, unit_cost_mean,
    unit_co2_min, unit_co2_max, unit_co2_mean, 
    # co2_ref
  ) %>%
  # filter(substr(component, 1, 1) != "2") %>%
  gt() %>%
  fmt_number(
    columns = c("min", "max", "mode"),
    decimals = 1
  ) %>%
  fmt_number(
    columns = matches("cost"),
    n_sigfig = 3
  ) %>%
  fmt_number(
    columns = matches("co2"),
    n_sigfig = 2
  ) %>%
  tab_spanner(
    label = "Fragility",
    columns = c("min", "max", "mode")
  ) %>%
  tab_spanner(
    label = "Replacement Cost ($)",
    columns = matches("cost"),
    id = "cost"
  ) %>%
  tab_spanner(
    label = md("GHG Emissions (CO~2eq~)"),
    columns = matches("co2")
  ) %>%
  tab_footnote(
    footnote = "(Doheny, 2021a)",
    locations = cells_column_spanners(spanners = "cost")
  ) %>%
  tab_footnote(
    footnote = "GHG emissions source: (NIST, 2023)",
    locations = cells_body(columns = component, rows = nist_index)
  ) %>%
  tab_footnote(
    footnote = "GHG emissions source: (ecoinvent, 2023)",
    locations = cells_body(columns = component, rows = ecoinvent_index)
  ) %>%
  tab_footnote(
    footnote = "GHG emissions source: (Adhikari et al., 2022; Silva et al., 2021)",
    locations = cells_body(columns = component, rows = adhikari_silva_index)
  ) %>%
  tab_footnote(
    footnote = "GHG emissions source: (Raluy and Dias, 2020)",
    locations = cells_body(columns = component, rows = raluy_index)
  ) %>%
  cols_label(
    component = "Component",
    unit = "Unit",
    unit_cost_min = "min",
    unit_cost_max = "max",
    unit_cost_mean = "mean",
    unit_co2_min = "min",
    unit_co2_max = "max",
    unit_co2_mean = "mean",
    # co2_ref = "Ref."
  )


### Study regions map --------

#TODO: add region labels

tract_results[tract_results$region.x == "paducah_cairo",]$region.x <- "Paducah-Cairo"
tract_results[tract_results$region.x == "burlington_davenport",]$region.x <- "Burlington-Davenport"


bdmap <- ggplot() +
  geom_sf(
    tract_results %>% filter(region.y == "burlington_davenport"),
    mapping = aes(geometry = geometry)
  ) +
  geom_sf(
    bd_streams,
    mapping = aes(geometry = x),
    color = "blue"
  )

pcmap <- ggplot() +
  geom_sf(
    tract_results %>% filter(region.y == "paducah_cairo"),
    mapping = aes(geometry = geometry)
  ) +
  geom_sf(
    pc_streams,
    mapping = aes(geometry = x),
    color = "blue"
  )
  

### Damage curve compare -------


dd_curves <- dd_curves %>%
  mutate(
    occdesc = if_else(
      occtype == "RES1-1S",
      "One Story",
      "Two Story"
    ),
    Source = source
  )

p <- ggplot(dd_curves) +
  geom_ribbon(
    aes(
      x = flood_depth,
      ymin = dmg_low_fix,
      ymax = dmg_high,
      fill = Source
    ),
    alpha = 0.4
  ) +
  geom_line(
    aes(
      x = flood_depth,
      y = dmg_mean,
      color = Source
    ),
    lwd = 1.5
  ) +
  scale_y_continuous(
    labels = scales::percent
  ) +
  labs(
    # title = "Depth-Damage Curves for Single-Family Residential Structures",
    x = "Flood Depth (ft)",
    y = "Damage Cost\n(% Structure Value)"
  ) +
  theme_paper() +
  theme(
    legend.position = 'bottom',
  ) +
  facet_wrap(~ occdesc)

ggsave(
  "../manuscript/figures/fig-compare.png",
  plot = p,
  width = 8,
  height = 5,
  units = "in",
  dpi = 400
)

### Study damage functions --------

#TODO: use cowplot to combine these two plots

dd_curves_study <- dd_curves_study %>%
  mutate(
    occdesc = if_else(
      occtype == "RES1-1S",
      "One Story",
      "Two Story"
    )
  )

p1 <- ggplot(dd_curves_study) +
  geom_ribbon(
    aes(
      x = flood_depth,
      ymin = co2_low/1000,
      ymax = co2_high/1000
    ),
    alpha = 0.4
  ) +
  geom_line(
    aes(
      x = flood_depth,
      y = co2_mean/1000
    ),
    lwd = 1.5
  ) +
  labs(
    # title = "Depth-Emissions Curves for Single-Family Residential Structures",
    x = "Flood Depth (ft)",
    y = "GHG Emissions\n(1000 kg CO2eq)"
  ) +
  facet_wrap(~ occdesc, nrow = 1) +
  theme_paper()

ggsave(
  "../manuscript/figures/ga-emissions.png",
  plot = p1,
  width = 8,
  height = 10,
  units = "in",
  dpi = 400
)

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
    y = "Social Cost of GHG Emissions\n(% Structure Value)"
  ) +
  facet_wrap(~ occdesc) +
  theme_paper() +
  theme(
    strip.text = element_blank()
  )

p3 <- plot_grid(p1, p2, nrow = 2, align = 'v')

ggsave(
  "../manuscript/figures/fig-emissions.png",
  plot = p3,
  width = 10,
  height = 8,
  units = "in",
  dpi = 400
)

### Regression --------

#TODO: add results table to figure

p7 <- ggplot(mcs_results, aes(
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
  # stat_poly_eq() +
  theme_paper()


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

t3 <- model %>%
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
  opt_stylize(
    style = 1,
    color = "gray",
    add_row_striping = FALSE
  )

gtsave(t3, "../manuscript/figures/tbl-regression.html")



p_reg <- ggdraw() +
  draw_plot(p7) +
  draw_image("../manuscript/figures/tbl-regression.png", .55, 0.05, .4, .3)

p_combined <- plot_grid(p3, p_reg, nrow = 1, labels = c('A', 'B'))

ggsave(
  "../manuscript/figures/fig-combined.png",
  plot = p_combined,
  width = 16,
  height = 10,
  units = "in",
  dpi = 400
)




### Region-tract results --------

tract_results <- tract_results %>%
  mutate(
    pct_change_mean = pct_change_mean - 1,
    region = gsub(
      "burlington_davenport",
      "Burlington-Davenport",
      gsub(
        "paducah_cairo",
        "Paducah-Cairo",
        region.x
      )
    )
  ) 



bd_tract <- tract_results %>%
  filter(region.x == "Burlington-Davenport")

pc_tract <- tract_results %>%
  filter(region.x == "Paducah-Cairo")

library(tmap)

reg_labs <- tibble(
  'x' = c(-90.5, -89),
  'y' = c(42.4, 38.4),
  'name' = c("Burlington-Davenport", "Paducah-Cairo")
) %>%
  st_as_sf(coords = c('x', 'y')) %>%
  st_set_crs(st_crs(tract_results))



pct_change <- ggplot(tract_results) +
  geom_sf(
    aes(fill = pct_change_mean),
    color = NA
  ) +
  # coord_sf(xlim = c(-92.5, -85)) +
  geom_sf_label(
    data = reg_labs,
    aes(label = name)
  ) +
  labs(
    x = '',
    y = ''
  ) +
  scale_fill_distiller(
    name = "Percent Change",
    labels = scales::percent,
    palette = "YlOrRd",
    direction = 1,
    limits = c(
      0,
      max(tract_results$pct_change_mean, na.rm = T)
    ),
    breaks = c(0, 0.04, 0.08, 0.12, 0.155)
  ) +
  theme_paper() +
  theme(legend.position = 'none')

ggplot(tract_results) +
  geom_point(
    aes(x = pct_change_mean, y = dmg_mean_sum)
  ) +
  scale_x_continuous(labels = scales::percent) +
  labs(
    x = "Percent Change",
    y = "Damage Cost"
  ) +
  theme_paper()



ggsave(
  "../manuscript/figures/ga-pctchange.png",
  plot = pct_change,
  width = 8,
  height = 10,
  units = "in",
  dpi = 400
)




### SVI Results --------

svi <- tract_results %>%
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
  ggplot(aes(x = rpl_themes, y = pct_change_mean)) +
  geom_point() +
  stat_poly_line() +
  stat_poly_eq() +
  labs(
    x = "Social Vulnerability Index",
    y = "Cost Increase From GHG"
  ) +
  scale_y_continuous(labels = scales::percent) +
  facet_wrap(~ region, nrow = 2) +
  theme_paper()

ggsave(
  "../manuscript/figures/fig-svi.png",
  plot = svi,
  width = 10,
  height = 8,
  units = "in",
  dpi = 400
)

ggplot(dd_curves_usace) +
  geom_line(
    aes(
      x=flood_depth,
      y=dmg_mean,
      color=occtype
    ),
    lwd=1
  ) +
  scale_y_continuous(labels = scales::percent_format()) +
  labs(
    x="Flood Depth (ft)",
    y="Damage"
  )

dd_x <- seq(-1, 20, 0.2)
dd_y <- sqrt(dd_x/20)

dd_curves_example <- data.frame(
  depth = dd_x,
  dmg = dd_y
)

dd_curves_example[is.na(dd_curves_example$dmg),]$dmg <- 0

table(dd_curves$source)
colnames(dd_curves)

dd_curves %>%
  filter(
    source == "GO Consequences: FEMA PFRA",
    occtype == "RES1-1S",
    flood_depth >= 0,
  ) %>%
  ggplot(aes(x=flood_depth, y = dmg_mean)) +
  geom_line(
    lwd = 2
  ) +
  scale_y_continuous(
    labels = scales::percent_format(),
    limits = c(0,1)
  ) +
  theme_paper() +
  labs(
    title = "FEMA Depth-Damage Curve",
    x = "Flood Depth (ft)",
    y = "Building Damage"
  )
