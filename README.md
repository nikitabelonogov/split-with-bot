# [@Split with Bot](https://t.me/split_with_bot)
This telegram bot helps you to split a receipts with your friends

## Usage
| command               | notes                                               |
|-----------------------|-----------------------------------------------------|
| `lend`                | lend \[name\] \[sum\] \[users...\]                  |
| `add`                 | alias for `lend`                                    |
| `lend_self_except`    | lend except your self \[name\] \[sum\] \[users...\] |
| `add_self_except`     | alias for `lend_self_except`                        |
| `history`             | show history of debts related to you                |
| `status`              | show your totals                                    |
| `help`                | show help                                           |

## Deployment
### Evironment Variables
| environment variable  | notes                   |
|-----------------------|-------------------------|
| TOKEN                 | telegram bot token      |
| DATABASE_URL          | database connection url |
| MODE                  | `webhook` or `polling`  |
| URL                   | heroku app url          |
| PORT                  | heroku app port         |
| DEBUG                 | debug                   |

## License
This project is licensed under [GLWTPL](./LICENSE)
