setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

library(tidyverse)
library(zoo)
library(readxl)
library(arrow)
library(data.table)

dfs <- read_xlsx("g2crm_res1-2_damage_fns.xlsx", sheet = "dfs")
colnames(dfs)

interpolation_cols <- setdiff(
  c(paste0("fd", seq(-9, 24, 0.1))),
  colnames(dfs)
)

dfs[interpolation_cols] <- NA

setDT(dfs)
depth_damage <- dfs %>%
  pivot_longer(
    cols = starts_with("fd"),
    names_to = "depth",
    values_to = "dmg_pct",
    names_prefix = "fd",
    names_transform = list(depth = as.numeric)
  ) %>%
  group_by(
    occtype, level
  ) %>%
  arrange(depth, .by_group = TRUE) %>%
  mutate(
    dmg_pct = na.approx(dmg_pct)
  ) %>%
  pivot_wider(
    names_from = level,
    names_glue = "dmg_pct_{level}",
    values_from = dmg_pct
  ) %>%
  select(
    occtype, flood_depth = depth, dmg_low = dmg_pct_min, dmg_mean = dmg_pct_mode, dmg_high = dmg_pct_max
  )


setDT(depth_damage)

head(depth_damage[flood_depth == 1.1 ,])

ggplot(depth_damage[occtype == "RES-1SNB"]) +
  geom_ribbon(aes(x = depth, ymin = dmg_pct_min, ymax = dmg_pct_max), alpha = 0.2) +
  geom_line(aes(x = depth, y = dmg_pct_mode))

write_parquet(depth_damage, "g2crm_dmg_fns.parquet")
