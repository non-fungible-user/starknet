# Starknet aio

Статья на teletype: https://teletype.in/@bxm/starknet-aio-settings

#### *Установка для Windows:*

Обязательно выполнить действия из данной инструкции:

https://sybil-v-zakone.notion.site/sybil-v-zakone/starknet-py-578a3b2fb96e49149a52b987cbbb8c73

После того, как выполнили действия из инструкции, выполняем данные команды в терминале:

1. `cd путь\к\проекту`
2. `python -m venv venv`
3. `.\venv\Scripts\activate`
4. `pip install -r requirements.txt`

#### *Установка для MacOS/Linux:*

Выполняем данные команды в терминале:

1. `cd путь/к/проекту`
2. `python3 -m venv venv`
3. MacOS/Linux `source venv/bin/activate`
4. `pip install -r requirements.txt`

#### *Настройка:*

Все настройки софта находятся в файле `config.py`

* `EVM_PRIVATE_KEYS_PATH` путь к файлу, содержащий приватные ключи EVM кошельков
* `STARKNET_PRIVATE_KEYS_PATH` путь к файлу, содержащий приватные ключи Starknet кошельков
* `PROXIES_PATH` путь к файлу с прокси, формат `user:pass@ip:port`
* `WITHDRAWAL_ADDRESSES` путь к файлу со Starknet адресами для выводов
* `DATABASE_PATH` путь к файлу с базой данных
* `TG_TOKEN` токен от телеграм бота
* `TG_IDS` id от аккаунтов телеграм, которым нужно отсылать телеграм логи
* `ATTEMPTS_COUNT` количество попыток, в случае ошибки
* `STARKNET_RPC_PROVIDER` RPC url. Обязательно ставьте alchemy / infura, они бесплатные. Используются только для получения баланса токенов на кошельке, но их использование обязательно для нормальной работы софта. Для себя мы выбираем alchemy
* `STARKNET_ESTIMATED_FEE_MULTIPLIER` мультипликатор эстимента газа для Starknet (лучше оставить 1.2)
* `EVM_ESTIMATED_FEE_MULTIPLIER` мультипликатор эстимента газа для EVM (лучше оставить 1.2)
* `USE_PROXY` если используете прокси - True, если нет - False
* `USE_MOBILE_PROXY` если используете мобильные прокси - True, если нет или не используете прокси вовсе - False
* `IP_CHANGE_LINK` ссылка на смену ip адреса, если используете мобильные прокси
* `GAS_THRESHOLD` максимальная плата за газ в сети ERC-20 при которой транзакции будут отправляться, значение в GWEI
* `GAS_DELAY_RANGE` диапазон для времени задержки между проверками текущей платы за газ в секундах
* `TX_DELAY_RANGE` диапазон времени задержки между отправкой каждой транзакции в секундах
* `STARKNET_ETH_MIN_BALANCE` минимальный баланс ETH в Starknet, если баланс ниже минимально, аккаунт пропускается. Также используется как ETH_SAFE_DEPOSIT
* `EVM_ETH_MIN_BALANCE` минимальный баланс ETH в EVM, если баланс ниже минимально, аккаунт пропускается
* `WALLET_APPLICATION` приложение, с помощью которого был сгенерирован кошелек starknet: "argentx" либо "braavos"
* `SLIPPAGE` процент slippage использующийся на всех dex, задается в процентах, например 2.5 это 2.5%
* `SWAP_DEVIATION` процент токенов для свапа от баланса монеты (например, 0.9 это 90%, а 0.33 это 33%)
* `ROUND_TO` количество знаков после запятой до скольки округлять число
* `DMAIL_TX_COUNT` количество транзакций dmail
* `NFT_MARKETPLACE_ALLOWANCE_TX_COUNT` количество allowance транзакций для nft маркетплейса
* `MYSWAP_SWAP_TX_COUNT` количество swap транзакций Myswap
* `JEDISWAP_SWAP_TX_COUNT` количество swap транзакций Jediswap
* `TENKSWAP_SWAP_TX_COUNT` количество swap транзакций 10kswap
* `SITHSWAP_SWAP_TX_COUNT` количество swap транзакций Sithswap
* `AVNU_SWAP_TX_COUNT` количество swap транзакций Avnu
* `MY_IDENTITY_MINT_TX_COUNT` количество swap транзакций My identity (бесплатная NFT на starknet id)
* `ZKLEND_TX_COUNT` количество раз, сколько добавить и достать ETH в Zklend (1 tx это 1 раз добавить и 1 раз достать)
* `WITHDRAWAL_FROM_ZKLEND` если нужно выводить из Zklend, то ставить True, а если только депозит, то False
* `ZKLEND_DEPOSIT_AMOUNT` количество ETH, которое будет добавлено в Zklend и после выведено оттуда
* `NFT_MARKETPLACE_ALLOWANCE_AMOUNT` количество ETH, которое будет дано апрувом на контракт nft маркетплейса (по сути оффер на nft)
* `OKX_API_KEY` API  ключ от API main аккаунта OKX
* `OKX_API_SECRET` SECRET ключ от API main аккаунта OKX
* `OKX_API_PASSWORD` PASSWORD ключ от API main аккаунта OKX
* `OKX_TOTAL_TRIES` количество попыток, в случае ошибки
* `OKX_SLEEP_TIME_AFTER_ERROR_SEC` количество секунд ожидания перед новой попыткой вывода после ошибочной
* `OKX_WITHDRAW_DEVIATION` количество токенов для вывода (например, 0.9 это 90%, а 0.33 это 33%)
* `OKX_WAIT_FOR_WITHDRAWAL_FINAL_STATUS_SEC` количество секунд ожидания перед новой попыткой проверки вывода
* `OKX_WAIT_FOR_WITHDRAWAL_FINAL_STATUS_ATTEMPTS` количество попыток проверки успешного вывода
* `OKX_WAIT_FOR_WITHDRAWAL_RECEIVED_ATTEMPTS` количество попыток проверки получения средств на кошелек
* `OKX_WAIT_FOR_WITHDRAWAL_RECEIVED_SLEEP_SEC` количество секунд ожидания перед новой попыткой проверки получения средств на кошелек

#### *Запуск:*

1. В `data/starknet_private_keys.txt` записываете приватные ключи Starknet (argentx или braavos)
2. В `data/evm_private_keys.txt` записываете приватные ключи EVM
3. В `data/withdrawal_addresses` записываете адреса Starknet для вывода ETH на OKX
4. В `data/proxies` записываете прокси в формате `user:pass@ip:port`

Пишем в консоли `python main.py` на Windows или `python3 main.py` на MacOS/Linux
