create database testchat;
CREATE SEQUENCE ids;

grant all privileges on database testchat to user1;
GRANT ALL PRIVILEGES ON sequence ids to user1;

\connect testchat;

Create table users (
    id INTEGER PRIMARY KEY DEFAULT NEXTVAL('ids'),
    name char(20),
    password char(20),
    avatar char(80),
    status char(10);

create table messages (
	id INTEGER PRIMARY KEY DEFAULT NEXTVAL('ids'),
	sender_id integer references users (id), 
	receiver_id integer references users (id),
	message char(100),
	time char(30));

insert into users (name, password, avatar, status) values ('name1', 'password1', '', 'ofline');
insert into users (name, password, avatar, status) values ('name2', 'password2', '', 'ofline');
insert into messages (sender_id, receiver_id, message, time) values (1,2,'Hello1', '123');

GRANT ALL PRIVILEGES ON TABLE users to user1;
GRANT ALL PRIVILEGES ON TABLE messages to user1;