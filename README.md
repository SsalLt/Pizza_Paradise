# Pizza_Paradise
## Техническое задание: Сайт пиццерии "PizzaParadise"

Цель проекта:
Разработать веб-приложение для пиццерии _"PizzaParadise"_, которое позволит пользователям просматривать меню, читать отзывы, добавлять отзывы, управлять корзиной для заказа пиццы, а также регистрироваться и входить в систему.

### Функциональные требования:

- Главная страница:
   - Отображает информацию о пиццерии и ее основные преимущества.
   - Содержит ссылки на разделы: "Меню", "О нас", "Отзывы", "Корзина".
   - Предоставляет возможность входа в систему или регистрации для пользователей.

- Страница "Меню":
   - Отображает список доступных пицц с их названиями, ценами и описанием.
   - Предоставляет возможность добавления пиццы в корзину.

- Страница "О нас":
   - Содержит информацию о пиццерии, историю, философию компании и контактные данные.

- Страница "Отзывы":
   - Отображает список отзывов пользователей о пиццерии.
   - Позволяет пользователям оставить свой отзыв, включая оценку и комментарий.

- Страница "Корзина":
   - Отображает список выбранных пицц и их цены в корзине.
   - Предоставляет возможность изменения количества пицц или удаления их из корзины.
   - Предоставляет кнопку для оформления заказа.

- Страница входа/регистрации:
   - Предоставляет формы для входа в систему или регистрации нового пользователя.
   - В случае успешного входа или регистрации перенаправляет пользователя на главную страницу.

### Нефункциональные требования:

- Безопасность:
   - Данные пользователей должны храниться в безопасной базе данных с защитой от несанкционированного доступа.
   - Пароли пользователей должны храниться в зашифрованном виде.

- Интерфейс:
   - Интерфейс должен быть интуитивно понятным и привлекательным для пользователей.
   - Страницы должны быть адаптированы для просмотра как на компьютере, так и на мобильных устройствах.

- Производительность:
   - Сайт должен обеспечивать быструю загрузку страниц и быструю обработку запросов.
   - При большой нагрузке система должна оставаться стабильной и отзывчивой.

- Масштабируемость:
   - Архитектура системы должна быть гибкой и масштабируемой для возможности добавления новых функций в будущем.

- Доступность:
   - Сайт должен быть доступен 24/7 для пользователей.

Технологии:
- Язык программирования: Python
- Фреймворк: Flask
- HTML, CSS, JavaScript для фронтенда
- SQLite для базы данных

Архитектура:
- MVC (Model-View-Controller)

Авторизация:
- Сессионная авторизация на основе cookies.

Развитие:
- В будущем может быть добавлен функционал онлайн-заказа с доставкой.
- Возможность оценивать отзывы других пользователей.

Важно:
Для успешной реализации проекта необходимо тщательное тестирование всех функций и обеспечение безопасности данных пользователей.