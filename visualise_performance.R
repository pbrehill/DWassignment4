# Title     : TODO
# Objective : TODO
# Created by: patrickrehill
# Created on: 26/2/21

library('tidyverse')

# Attrs blocking

attrsblocking_df <- read_csv('recordLinkage.py-blocking_attrs-blocking.csv')

# Add comma after blocking vars to make it easier to distinguish 1 from 11
attrsblocking_df$blocking_attrs_re <- str_replace(attrsblocking_df$blocking_attrs, '\\]', ',]') %>%
    str_replace('\\[', '[ ')

included_attrs <- c(' 1,', ' 2,', ' 3,', ' 4,', ' 5,', ' 6,', ' 7,', ' 8,', ' 9,', ' 10,', ' 11,') %>%
    set_names(.,.) %>%
    map_df(~str_detect(attrsblocking_df$blocking_attrs_re, .x))

included_attrs[is.na(included_attrs)] <- FALSE

names(included_attrs) <- as.character(1:11)

combined_df <- bind_cols(included_attrs, attrsblocking_df)

means <- 1:11 %>%
    map_df(~attrsblocking_df[included_attrs[.x] %>% pull() ,] %>%
        summarise_if(is.numeric, mean, na.rm = TRUE))

print(head(means))
write.csv(means, 'mean_by_attribute.csv')
