# Title     : TODO
# Objective : TODO
# Created by: patrickrehill
# Created on: 27/2/21

library(tidyverse)

# Import data, put them in a list
df1 <- read_csv()
df2 <- read_csv()
df_ls <- list(df1, df2)


# Count the blanks
blanks_count <- df_ls %>%
    map(function (x) {
        x %>%
            map(function (y) {
                sum(is.na(.x))
            })
    })

valid_name <- function (x) is.character(x) & length(x) > 1
valid_age <- function (x) is.numeric(x) & x > -1 & x < 150
valid_date <- function (x) str_detect(x, '^[:digit:][:digit:]/[:digit:][:digit:]/[:digit:][:digit:]$')
valid_postcode <- function (x) {
    str_detect(x, '^[:digit:]{4}$') |
        str_detect(x, '^8[:digit:]{2}$') |
        str_detect(x, '^9[:digit:]{2}$')
}
valid_state <- function (x) x %in% c('VIC', 'NSW', 'QLD', 'ACT', 'SA', 'WA', 'NT', 'TAS')
valid_phone <- function (x) str_detect(x, '^[:digit:]{2} [:digit:]{4} [:digit:]{4}$')
# There are some emails with corrupted top-level domains, but given new tlds I didn't want to add a check for valid domain.
valid_email <- function (x) str_detect(x, '@') & str_detect(x, '\\.')


# Count the formating
count_appropriate <- function (df) {
    # First name
    # Note I'm assuming anything of length 1 is an initial
    first_name <- sum(valid_name(df$first_name))
    middle_name <- sum(valid_name(df$middle_name))
    last_name <- sum(valid_name(df$last_name))
    current_age <- sum(valid_age(df$current_age))
    # I'm going to ignore address because while there may be legitimate issues e.g. no numbers, there are legit reasons this may occur
    birth_date <- sum(valid_date(df$birth_date))
    postcode <- sum(valid_postcode(df$postcode))
    state <- sum(valid_state(df$state))
    phone <- sum(valid_phone(df$phone))
    email <- sum(valid_email(df$email))

    c(first_name, middle_name, last_name, current_age, birth_date, postcode, state, phone, email)

}
