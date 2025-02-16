--
-- PostgreSQL database dump
--

-- Dumped from database version 16.0
-- Dumped by pg_dump version 16.0

-- Started on 2025-02-16 20:56:48 MSK

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 242 (class 1255 OID 16710)
-- Name: create_credit_and_repayment(integer, integer, date, money, date, numeric, money); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.create_credit_and_repayment(IN in_id_client integer, IN in_id_credit_product integer, IN in_crt_date_issue date, IN in_crt_monthly_contributions money, IN in_crt_maturity_date date, IN in_crt_percent_on_credit numeric, IN in_crt_sum_credit money)
    LANGUAGE plpgsql
    AS $$
DECLARE
existing_credit_count INT4;
out_id_credit INT4;
BEGIN

SELECT COUNT(*) INTO existing_credit_count
FROM credit
WHERE id_client = in_id_client;

IF existing_credit_count > 0 THEN

INSERT INTO credit (
id_client,
id_credit_product,
crt_date_issue,
crt_monthly_contributions,
crt_maturity_date,
crt_percent_on_credit,
crt_status_credit,
crt_sum_credit
) VALUES (
in_id_client,
in_id_credit_product,
in_crt_date_issue,
in_crt_monthly_contributions,
in_crt_maturity_date,
in_crt_percent_on_credit,
'2',
in_crt_sum_credit
);

ELSE

INSERT INTO credit (
id_client,
id_credit_product,
crt_date_issue,
crt_monthly_contributions,
crt_maturity_date,
crt_percent_on_credit,
crt_status_credit,
crt_sum_credit
) VALUES (
in_id_client,
in_id_credit_product,
in_crt_date_issue,
in_crt_monthly_contributions,
in_crt_maturity_date,
in_crt_percent_on_credit,
'1',
in_crt_sum_credit
) RETURNING id_credit INTO out_id_credit;

INSERT INTO loan_repayments (
id_client,
id_credit,
lnr_date_deposit,
lnr_amount_payments,
lnr_contribution_status
) VALUES (
in_id_client,
out_id_credit,
in_crt_date_issue,
in_crt_monthly_contributions,
'1'
);
END IF;
END;
$$;


ALTER PROCEDURE public.create_credit_and_repayment(IN in_id_client integer, IN in_id_credit_product integer, IN in_crt_date_issue date, IN in_crt_monthly_contributions money, IN in_crt_maturity_date date, IN in_crt_percent_on_credit numeric, IN in_crt_sum_credit money) OWNER TO postgres;

--
-- TOC entry 228 (class 1255 OID 16681)
-- Name: set_default_issue_date(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_default_issue_date() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.crt_date_issue IS NULL THEN
NEW.crt_date_issue := CURRENT_DATE;
END IF;
RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_default_issue_date() OWNER TO postgres;

--
-- TOC entry 229 (class 1255 OID 16691)
-- Name: set_default_repayment_amount(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_default_repayment_amount() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.lnr_amount_payments IS NULL THEN
SELECT crt_monthly_contributions INTO NEW.lnr_amount_payments
FROM credit
WHERE id_credit = NEW.id_credit;
END IF;

RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_default_repayment_amount() OWNER TO postgres;

--
-- TOC entry 230 (class 1255 OID 16695)
-- Name: set_maturity_date_from_product(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_maturity_date_from_product() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.crt_maturity_date IS NULL AND NEW.id_credit_product IS NOT NULL THEN
SELECT cpr_max_date_return INTO NEW.crt_maturity_date
FROM credit_products
WHERE id_credit_product = NEW.id_credit_product;
END IF;
RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_maturity_date_from_product() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 216 (class 1259 OID 16570)
-- Name: client; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client (
    id_client integer NOT NULL,
    clt_last_name character varying(32) NOT NULL,
    clt_name character varying(32) NOT NULL,
    clt_middle_name character varying(32),
    clt_date_birth date NOT NULL,
    clt_residential_address character varying(64) NOT NULL,
    clt_income money NOT NULL,
    clt_passport_data character varying(10) NOT NULL,
    clt_marital_status character varying(1) NOT NULL
);


ALTER TABLE public.client OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 16569)
-- Name: client_id_client_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.client_id_client_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.client_id_client_seq OWNER TO postgres;

--
-- TOC entry 3705 (class 0 OID 0)
-- Dependencies: 215
-- Name: client_id_client_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.client_id_client_seq OWNED BY public.client.id_client;


--
-- TOC entry 218 (class 1259 OID 16578)
-- Name: credit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.credit (
    id_credit integer NOT NULL,
    id_client integer NOT NULL,
    id_credit_product integer NOT NULL,
    crt_date_issue date,
    crt_monthly_contributions money NOT NULL,
    crt_maturity_date date NOT NULL,
    crt_percent_on_credit numeric(5,2) NOT NULL,
    crt_status_credit character varying(1) NOT NULL,
    crt_sum_credit money NOT NULL
);


ALTER TABLE public.credit OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16588)
-- Name: credit_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.credit_history (
    id_credit_history integer NOT NULL,
    id_client integer NOT NULL,
    id_credit integer NOT NULL,
    chs_amount_debt money NOT NULL,
    chs_loan_status character varying(1) NOT NULL
);


ALTER TABLE public.credit_history OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16587)
-- Name: credit_history_id_credit_history_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.credit_history_id_credit_history_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.credit_history_id_credit_history_seq OWNER TO postgres;

--
-- TOC entry 3706 (class 0 OID 0)
-- Dependencies: 219
-- Name: credit_history_id_credit_history_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.credit_history_id_credit_history_seq OWNED BY public.credit_history.id_credit_history;


--
-- TOC entry 217 (class 1259 OID 16577)
-- Name: credit_id_credit_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.credit_id_credit_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.credit_id_credit_seq OWNER TO postgres;

--
-- TOC entry 3707 (class 0 OID 0)
-- Dependencies: 217
-- Name: credit_id_credit_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.credit_id_credit_seq OWNED BY public.credit.id_credit;


--
-- TOC entry 222 (class 1259 OID 16598)
-- Name: credit_products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.credit_products (
    id_credit_product integer NOT NULL,
    cpr_name_product character varying(16) NOT NULL,
    cpr_min_koef numeric(5,2) NOT NULL,
    cpr_max_koef numeric(5,2),
    cpr_min_date_return date NOT NULL,
    cpr_max_date_return date
);


ALTER TABLE public.credit_products OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16597)
-- Name: credit_products_id_credit_product_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.credit_products_id_credit_product_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.credit_products_id_credit_product_seq OWNER TO postgres;

--
-- TOC entry 3708 (class 0 OID 0)
-- Dependencies: 221
-- Name: credit_products_id_credit_product_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.credit_products_id_credit_product_seq OWNED BY public.credit_products.id_credit_product;


--
-- TOC entry 224 (class 1259 OID 16606)
-- Name: loan_repayments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.loan_repayments (
    id_payout integer NOT NULL,
    id_client integer NOT NULL,
    id_credit integer NOT NULL,
    lnr_date_deposit date NOT NULL,
    lnr_amount_payments money NOT NULL,
    lnr_contribution_status character varying(1) NOT NULL
);


ALTER TABLE public.loan_repayments OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16605)
-- Name: loan_repayments_id_payout_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.loan_repayments_id_payout_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_repayments_id_payout_seq OWNER TO postgres;

--
-- TOC entry 3709 (class 0 OID 0)
-- Dependencies: 223
-- Name: loan_repayments_id_payout_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.loan_repayments_id_payout_seq OWNED BY public.loan_repayments.id_payout;


--
-- TOC entry 225 (class 1259 OID 16661)
-- Name: number; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.number (
    numbers integer NOT NULL
);


ALTER TABLE public.number OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16740)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(255) NOT NULL,
    role character varying(50) DEFAULT 'user'::character varying NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16739)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 3710 (class 0 OID 0)
-- Dependencies: 226
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3498 (class 2604 OID 16573)
-- Name: client id_client; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client ALTER COLUMN id_client SET DEFAULT nextval('public.client_id_client_seq'::regclass);


--
-- TOC entry 3499 (class 2604 OID 16581)
-- Name: credit id_credit; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit ALTER COLUMN id_credit SET DEFAULT nextval('public.credit_id_credit_seq'::regclass);


--
-- TOC entry 3500 (class 2604 OID 16591)
-- Name: credit_history id_credit_history; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_history ALTER COLUMN id_credit_history SET DEFAULT nextval('public.credit_history_id_credit_history_seq'::regclass);


--
-- TOC entry 3501 (class 2604 OID 16601)
-- Name: credit_products id_credit_product; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_products ALTER COLUMN id_credit_product SET DEFAULT nextval('public.credit_products_id_credit_product_seq'::regclass);


--
-- TOC entry 3502 (class 2604 OID 16609)
-- Name: loan_repayments id_payout; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_repayments ALTER COLUMN id_payout SET DEFAULT nextval('public.loan_repayments_id_payout_seq'::regclass);


--
-- TOC entry 3503 (class 2604 OID 16743)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3688 (class 0 OID 16570)
-- Dependencies: 216
-- Data for Name: client; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client (id_client, clt_last_name, clt_name, clt_middle_name, clt_date_birth, clt_residential_address, clt_income, clt_passport_data, clt_marital_status) FROM stdin;
11	Морозов	Игорь	Николаевич	1978-12-27	г Липецк ул. Ленина, 7	$350,000.00	0123456789	0
10	Новиков	Олег	Дмитриевич	1983-04-14	г Липецк ул. Гагарина, 10	$900,000.00	9012345678	1
9	Михайлов	Максим	Александрович	1995-06-19	г Липецк ул. Пушкина, 5	$250,000.00	8901234567	1
8	Соколова	Анна	Михайловна	1988-07-23	г Липецк ул. Ленина, 3	$600,000.00	7890123456	2
7	Попов	Николай	Игоревич	1975-02-08	г Липецк ул. Московская, 9	$800,000.00	6789012345	1
6	Васильев	Сергей	Петрович	1980-09-30	г Липецк ул. Советская, 12	$450,000.00	5678901234	0
5	Кузнецов	Денис	Владимирович	1990-11-05	г Липецк ул. Кирова, 21	$300,000.00	4567890123	0
4	Смирнова	Елена	Андреевна	1985-03-17	г Липецк ул. Гагарина, 3	$700,000.00	3456789012	1
3	Петров	Александр	Иванович	1992-08-24	г Липецк ул. Пушкина, 7	$500,000.00	2345678901	2
12	Леонидов	Максим	Юрьевич	2000-05-15	г Липецк ул Советская 24	$5,000.00	0000123456	0
16	Сморин	Алексей	Дмитриевич	1999-06-20	г Москва	$200.00	0000000000	2
17	Segeda	Arseniy	Владимирович	2000-10-03	г Липецк ул Космонавтов 23	$100,000.00	0909123456	1
22	Серпов1	Дмитрий	Владимирович	2000-10-03	г Липецк ул Космонавтов 23	$100,000.00	0909123456	1
37	Сегеда	Арсений	Николаевич	2001-01-01	Липецк	$1,000,000.00	1234987654	1
39	Денисов	Денис	Эдуардович	2003-01-01	Липецк	$10,000.00	1234987654	1
51	Ковач	Семен	Риц	2023-01-01	г Липецк	$20,000.00	1234567890	1
52	Сегеда	Арсений	Николаевич	2003-06-04	г Липецк	$0.00	1234567890	1
53	qwe	qwe	qwe	2000-01-01	qwe	$1,000.00	1234567890	1
\.


--
-- TOC entry 3690 (class 0 OID 16578)
-- Dependencies: 218
-- Data for Name: credit; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.credit (id_credit, id_client, id_credit_product, crt_date_issue, crt_monthly_contributions, crt_maturity_date, crt_percent_on_credit, crt_status_credit, crt_sum_credit) FROM stdin;
17	11	3	2023-10-10	$500.00	2024-10-10	0.25	1	$4,000.00
18	5	2	2023-10-10	$35,000.00	2033-11-10	0.10	1	$3,000,000.00
19	8	2	2023-11-12	$25,000.00	2053-12-12	0.15	0	$7,000,000.00
15	4	3	2023-11-10	$10,000.00	2026-11-10	0.25	1	$250,000.00
34	22	4	2023-12-26	$1,000.00	2023-12-26	0.10	1	$1,000,000.00
41	22	4	2023-01-01	$1,000.00	2028-01-01	0.30	1	$100,000,000.00
25	12	3	2022-12-14	$1,200.00	2023-12-14	0.30	2	$15,000.00
12	12	3	2022-01-01	$1,000.00	2023-01-01	0.30	2	$7,000.00
48	37	1	2023-01-01	$10,000.00	2023-12-31	0.10	1	$10,000.00
2	11	3	2023-11-12	$10,000.00	2024-12-12	0.30	1	$80,000.00
3	10	3	2023-10-10	$15,000.00	2026-11-10	0.25	0	$300,000.00
4	9	3	2023-11-10	$10,000.00	2025-12-10	0.25	1	$150,000.00
5	8	2	2023-11-12	$25,000.00	2053-12-12	0.15	0	$7,000,000.00
6	7	2	2023-10-10	$30,000.00	2053-12-10	0.15	1	$7,000,000.00
7	6	2	2023-11-12	$25,000.00	2043-12-12	0.10	1	$4,500,000.00
8	5	2	2023-10-10	$35,000.00	2033-11-10	0.10	1	$3,000,000.00
9	4	1	2023-11-10	$50,000.00	2053-12-10	0.05	1	$17,000,000.00
10	3	1	2023-10-10	$50,000.00	2053-11-10	0.10	1	$16,000,000.00
16	10	2	2023-11-12	$15,000.00	2053-11-12	0.15	1	$4,000,000.00
50	37	1	2023-01-01	$10,000.00	2023-12-31	0.10	2	$10,000.00
65	22	4	2024-06-04	$1,000.00	2028-01-01	0.30	1	$10,000,000.00
66	52	1	2024-06-05	$100,000.00	2034-06-05	0.20	0	$1,000,000.00
\.


--
-- TOC entry 3692 (class 0 OID 16588)
-- Dependencies: 220
-- Data for Name: credit_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.credit_history (id_credit_history, id_client, id_credit, chs_amount_debt, chs_loan_status) FROM stdin;
1	12	12	$7,000.00	0
3	12	25	$3,000.00	0
\.


--
-- TOC entry 3694 (class 0 OID 16598)
-- Dependencies: 222
-- Data for Name: credit_products; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.credit_products (id_credit_product, cpr_name_product, cpr_min_koef, cpr_max_koef, cpr_min_date_return, cpr_max_date_return) FROM stdin;
1	Ипотека	0.05	0.15	2028-01-01	2053-01-01
2	Автокредит	0.10	0.20	2033-01-01	2053-01-01
3	Потребительский	0.15	0.30	2025-01-01	2028-01-01
4	Рефинансирование	0.10	0.15	2025-01-01	2028-01-01
8	test	0.20	0.20	2023-01-01	2023-01-01
\.


--
-- TOC entry 3696 (class 0 OID 16606)
-- Dependencies: 224
-- Data for Name: loan_repayments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.loan_repayments (id_payout, id_client, id_credit, lnr_date_deposit, lnr_amount_payments, lnr_contribution_status) FROM stdin;
3	3	10	2023-11-10	$50,000.00	0
5	3	10	2023-12-10	$50,000.00	0
6	4	9	2023-12-10	$50,000.00	0
7	5	8	2023-11-10	$35,000.00	0
8	5	8	2023-11-10	$35,000.00	0
9	7	6	2023-12-12	$25,000.00	0
10	6	7	2023-11-10	$30,000.00	0
11	6	7	2023-12-10	$30,000.00	0
12	8	5	2023-12-12	$25,000.00	0
13	9	4	2023-12-10	$10,000.00	0
14	10	3	2023-11-10	$15,000.00	0
15	10	3	2023-11-10	$15,000.00	0
16	11	2	2023-12-12	$20,000.00	0
29	12	25	2023-01-14	$1,000.00	1
30	12	25	2023-02-14	$1,000.00	1
31	12	25	2023-03-14	$1,000.00	1
32	12	25	2023-04-14	$1,000.00	1
33	12	25	2023-05-14	$1,000.00	1
34	12	25	2023-06-14	$1,000.00	1
35	12	25	2023-07-14	$1,000.00	1
36	12	25	2023-08-14	$1,000.00	1
37	12	25	2023-09-14	$1,000.00	1
38	12	25	2023-10-14	$1,000.00	1
39	12	25	2023-11-14	$1,000.00	1
40	12	25	2023-12-14	$1,000.00	1
17	12	12	2022-02-01	$160,000.00	1
18	12	12	2022-03-01	$160,000.00	1
19	12	12	2022-04-01	$160,000.00	1
20	12	12	2022-05-01	$160,000.00	1
21	12	12	2022-06-01	$160,000.00	1
22	12	12	2022-07-01	$160,000.00	1
23	12	12	2022-08-01	$160,000.00	1
24	12	12	2022-09-01	$160,000.00	1
25	12	12	2022-10-01	$160,000.00	1
26	12	12	2022-11-01	$160,000.00	1
27	12	12	2022-12-01	$160,000.00	1
28	12	12	2023-01-01	$160,000.00	1
45	37	48	2023-01-01	$10,000.00	1
\.


--
-- TOC entry 3697 (class 0 OID 16661)
-- Dependencies: 225
-- Data for Name: number; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.number (numbers) FROM stdin;
12
11
10
9
8
7
6
5
4
3
2
1
\.


--
-- TOC entry 3699 (class 0 OID 16740)
-- Dependencies: 227
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password, role) FROM stdin;
2	user	scrypt:32768:8:1$C5SEsVSIdSz5Tvkp$fdb35474eb8de8d176f4cee1e74bd138b2796cc02ddd4a0674662f9bdffba7f5ef34526311534d01102c3be428425bc39f90d0d3a8206f370c32c92b018b0a23	user
1	admin	scrypt:32768:8:1$yQKoq8VQH49nFHaK$34ddfe8d1c5297c6514316cea78e06cc5b3bae48733ab9f860cbe5f50ef4968c98ad1152fbc0a8644b47bbab64725b4d1ae822af6bbc496390d059c8548736ed	admin
52	Arseniy	scrypt:32768:8:1$tnBnjQ38EB9Fu1jL$9afc8462d6341f4c9b1ea53669ac9341a030ba1459d6ccccb46c62a0ee6ddc64b7b073028e4d90c7f670ee7aaac320494b2079cefbc43c169b7f102e2f7bba02	admin
4	test13	test	user
53	qwe	scrypt:32768:8:1$RkAihTvmMkkB3VPk$df050d4716067bd9b36cdbcc927001f142a67d2345cbba297459b18caa4facaaebd6ccb1bcfab5b29d3c4f41b066e3a834c7143e6f72ac9446e1a996ddbf8cf3	user
\.


--
-- TOC entry 3711 (class 0 OID 0)
-- Dependencies: 215
-- Name: client_id_client_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.client_id_client_seq', 53, true);


--
-- TOC entry 3712 (class 0 OID 0)
-- Dependencies: 219
-- Name: credit_history_id_credit_history_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.credit_history_id_credit_history_seq', 7, true);


--
-- TOC entry 3713 (class 0 OID 0)
-- Dependencies: 217
-- Name: credit_id_credit_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.credit_id_credit_seq', 70, true);


--
-- TOC entry 3714 (class 0 OID 0)
-- Dependencies: 221
-- Name: credit_products_id_credit_product_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.credit_products_id_credit_product_seq', 8, true);


--
-- TOC entry 3715 (class 0 OID 0)
-- Dependencies: 223
-- Name: loan_repayments_id_payout_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.loan_repayments_id_payout_seq', 57, true);


--
-- TOC entry 3716 (class 0 OID 0)
-- Dependencies: 226
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 7, true);


--
-- TOC entry 3529 (class 2606 OID 16665)
-- Name: number number_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.number
    ADD CONSTRAINT number_pkey PRIMARY KEY (numbers);


--
-- TOC entry 3507 (class 2606 OID 16575)
-- Name: client pk_client; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT pk_client PRIMARY KEY (id_client);


--
-- TOC entry 3513 (class 2606 OID 16583)
-- Name: credit pk_credit; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit
    ADD CONSTRAINT pk_credit PRIMARY KEY (id_credit);


--
-- TOC entry 3519 (class 2606 OID 16593)
-- Name: credit_history pk_credit_history; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT pk_credit_history PRIMARY KEY (id_credit_history);


--
-- TOC entry 3522 (class 2606 OID 16603)
-- Name: credit_products pk_credit_products; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_products
    ADD CONSTRAINT pk_credit_products PRIMARY KEY (id_credit_product);


--
-- TOC entry 3527 (class 2606 OID 16611)
-- Name: loan_repayments pk_loan_repayments; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT pk_loan_repayments PRIMARY KEY (id_payout);


--
-- TOC entry 3532 (class 2606 OID 16746)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3534 (class 2606 OID 16748)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 3505 (class 1259 OID 16576)
-- Name: client_pk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX client_pk ON public.client USING btree (id_client);


--
-- TOC entry 3515 (class 1259 OID 16594)
-- Name: credit_history_pk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX credit_history_pk ON public.credit_history USING btree (id_credit_history);


--
-- TOC entry 3508 (class 1259 OID 16584)
-- Name: credit_pk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX credit_pk ON public.credit USING btree (id_credit);


--
-- TOC entry 3520 (class 1259 OID 16604)
-- Name: credit_products_pk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX credit_products_pk ON public.credit_products USING btree (id_credit_product);


--
-- TOC entry 3509 (class 1259 OID 16660)
-- Name: crt_date_issue; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX crt_date_issue ON public.credit USING btree (crt_date_issue);


--
-- TOC entry 3510 (class 1259 OID 16659)
-- Name: crt_sum_credit; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX crt_sum_credit ON public.credit USING btree (crt_sum_credit);


--
-- TOC entry 3511 (class 1259 OID 16586)
-- Name: has_credit_products_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX has_credit_products_fk ON public.credit USING btree (id_credit_product);


--
-- TOC entry 3516 (class 1259 OID 16595)
-- Name: has_history_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX has_history_fk ON public.credit_history USING btree (id_client);


--
-- TOC entry 3530 (class 1259 OID 16901)
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- TOC entry 3523 (class 1259 OID 16612)
-- Name: loan_repayments_pk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX loan_repayments_pk ON public.loan_repayments USING btree (id_payout);


--
-- TOC entry 3517 (class 1259 OID 16596)
-- Name: paid_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX paid_fk ON public.credit_history USING btree (id_credit);


--
-- TOC entry 3524 (class 1259 OID 16614)
-- Name: payments_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX payments_fk ON public.loan_repayments USING btree (id_credit);


--
-- TOC entry 3525 (class 1259 OID 16613)
-- Name: pays_out_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX pays_out_fk ON public.loan_repayments USING btree (id_client);


--
-- TOC entry 3514 (class 1259 OID 16585)
-- Name: registr_fk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX registr_fk ON public.credit USING btree (id_client);


--
-- TOC entry 3541 (class 2620 OID 16682)
-- Name: credit trigger_set_default_issue_date; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_set_default_issue_date BEFORE INSERT ON public.credit FOR EACH ROW EXECUTE FUNCTION public.set_default_issue_date();


--
-- TOC entry 3543 (class 2620 OID 16692)
-- Name: loan_repayments trigger_set_default_repayment_amount; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_set_default_repayment_amount BEFORE INSERT ON public.loan_repayments FOR EACH ROW EXECUTE FUNCTION public.set_default_repayment_amount();


--
-- TOC entry 3542 (class 2620 OID 16696)
-- Name: credit trigger_set_maturity_date; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_set_maturity_date BEFORE INSERT ON public.credit FOR EACH ROW EXECUTE FUNCTION public.set_maturity_date_from_product();


--
-- TOC entry 3537 (class 2606 OID 16922)
-- Name: credit_history fk_credit_h_has_histo_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT fk_credit_h_has_histo_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON DELETE CASCADE;


--
-- TOC entry 3538 (class 2606 OID 16937)
-- Name: credit_history fk_credit_h_paid_credit; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT fk_credit_h_paid_credit FOREIGN KEY (id_credit) REFERENCES public.credit(id_credit) ON DELETE CASCADE;


--
-- TOC entry 3535 (class 2606 OID 16615)
-- Name: credit fk_credit_has_credi_credit_p; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit
    ADD CONSTRAINT fk_credit_has_credi_credit_p FOREIGN KEY (id_credit_product) REFERENCES public.credit_products(id_credit_product) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3536 (class 2606 OID 16917)
-- Name: credit fk_credit_registr_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credit
    ADD CONSTRAINT fk_credit_registr_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON DELETE CASCADE;


--
-- TOC entry 3539 (class 2606 OID 16932)
-- Name: loan_repayments fk_loan_rep_payments_credit; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT fk_loan_rep_payments_credit FOREIGN KEY (id_credit) REFERENCES public.credit(id_credit) ON DELETE CASCADE;


--
-- TOC entry 3540 (class 2606 OID 16927)
-- Name: loan_repayments fk_loan_rep_pays_out_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT fk_loan_rep_pays_out_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON DELETE CASCADE;


-- Completed on 2025-02-16 20:56:48 MSK

--
-- PostgreSQL database dump complete
--

