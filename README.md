# [@Split with Bot](https://t.me/split_with_bot)
This telegram bot helps you to split a receipts with your friends

## Usage
| command               | notes                                               |
|-----------------------|-----------------------------------------------------|
| `split`               | lend a split check between users and you            |
| `lend`                | lend a split check between users                    |
| `history`             | show history of debts related to you                |
| `status`              | show your totals                                    |
| `delete`              | delete history                                      |
| `help`                | show help                                           |

## Deployment
### Environment Variables
| environment variable  | notes                   |
|-----------------------|-------------------------|
| TOKEN                 | telegram bot token      |
| DATABASE_URL          | database connection url |
| MODE                  | `webhook` or `polling`  |
| URL                   | heroku app url          |
| PORT                  | heroku app port         |
| DEBUG                 | debug                   |

### webhook mode
TBD

### pooling mode
TBD

## Heroku
database credentials
```shell
heroku config:get DATABASE_URL -a split-with-bot
```

## License
This project is licensed under [GLWTPL](./LICENSE)
