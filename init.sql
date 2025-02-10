PGDMP      1        
        }            labaratornaya    16.0    16.0 L    u           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            v           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            w           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            x           1262    16568    labaratornaya    DATABASE     �   CREATE DATABASE labaratornaya WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = icu LOCALE = 'en_US.UTF-8' ICU_LOCALE = 'en-US';
    DROP DATABASE labaratornaya;
                postgres    false            �            1255    16710 P   create_credit_and_repayment(integer, integer, date, money, date, numeric, money) 	   PROCEDURE     �  CREATE PROCEDURE public.create_credit_and_repayment(IN in_id_client integer, IN in_id_credit_product integer, IN in_crt_date_issue date, IN in_crt_monthly_contributions money, IN in_crt_maturity_date date, IN in_crt_percent_on_credit numeric, IN in_crt_sum_credit money)
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
   DROP PROCEDURE public.create_credit_and_repayment(IN in_id_client integer, IN in_id_credit_product integer, IN in_crt_date_issue date, IN in_crt_monthly_contributions money, IN in_crt_maturity_date date, IN in_crt_percent_on_credit numeric, IN in_crt_sum_credit money);
       public          postgres    false            �            1255    16681    set_default_issue_date()    FUNCTION     �   CREATE FUNCTION public.set_default_issue_date() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.crt_date_issue IS NULL THEN
NEW.crt_date_issue := CURRENT_DATE;
END IF;
RETURN NEW;
END;
$$;
 /   DROP FUNCTION public.set_default_issue_date();
       public          postgres    false            �            1255    16691    set_default_repayment_amount()    FUNCTION       CREATE FUNCTION public.set_default_repayment_amount() RETURNS trigger
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
 5   DROP FUNCTION public.set_default_repayment_amount();
       public          postgres    false            �            1255    16695     set_maturity_date_from_product()    FUNCTION     R  CREATE FUNCTION public.set_maturity_date_from_product() RETURNS trigger
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
 7   DROP FUNCTION public.set_maturity_date_from_product();
       public          postgres    false            �            1259    16570    client    TABLE     �  CREATE TABLE public.client (
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
    DROP TABLE public.client;
       public         heap    postgres    false            �            1259    16569    client_id_client_seq    SEQUENCE     �   CREATE SEQUENCE public.client_id_client_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.client_id_client_seq;
       public          postgres    false    216            y           0    0    client_id_client_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.client_id_client_seq OWNED BY public.client.id_client;
          public          postgres    false    215            �            1259    16578    credit    TABLE     |  CREATE TABLE public.credit (
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
    DROP TABLE public.credit;
       public         heap    postgres    false            �            1259    16588    credit_history    TABLE     �   CREATE TABLE public.credit_history (
    id_credit_history integer NOT NULL,
    id_client integer NOT NULL,
    id_credit integer NOT NULL,
    chs_amount_debt money NOT NULL,
    chs_loan_status character varying(1) NOT NULL
);
 "   DROP TABLE public.credit_history;
       public         heap    postgres    false            �            1259    16587 $   credit_history_id_credit_history_seq    SEQUENCE     �   CREATE SEQUENCE public.credit_history_id_credit_history_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ;   DROP SEQUENCE public.credit_history_id_credit_history_seq;
       public          postgres    false    220            z           0    0 $   credit_history_id_credit_history_seq    SEQUENCE OWNED BY     m   ALTER SEQUENCE public.credit_history_id_credit_history_seq OWNED BY public.credit_history.id_credit_history;
          public          postgres    false    219            �            1259    16577    credit_id_credit_seq    SEQUENCE     �   CREATE SEQUENCE public.credit_id_credit_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.credit_id_credit_seq;
       public          postgres    false    218            {           0    0    credit_id_credit_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.credit_id_credit_seq OWNED BY public.credit.id_credit;
          public          postgres    false    217            �            1259    16598    credit_products    TABLE       CREATE TABLE public.credit_products (
    id_credit_product integer NOT NULL,
    cpr_name_product character varying(16) NOT NULL,
    cpr_min_koef numeric(5,2) NOT NULL,
    cpr_max_koef numeric(5,2),
    cpr_min_date_return date NOT NULL,
    cpr_max_date_return date
);
 #   DROP TABLE public.credit_products;
       public         heap    postgres    false            �            1259    16597 %   credit_products_id_credit_product_seq    SEQUENCE     �   CREATE SEQUENCE public.credit_products_id_credit_product_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 <   DROP SEQUENCE public.credit_products_id_credit_product_seq;
       public          postgres    false    222            |           0    0 %   credit_products_id_credit_product_seq    SEQUENCE OWNED BY     o   ALTER SEQUENCE public.credit_products_id_credit_product_seq OWNED BY public.credit_products.id_credit_product;
          public          postgres    false    221            �            1259    16606    loan_repayments    TABLE       CREATE TABLE public.loan_repayments (
    id_payout integer NOT NULL,
    id_client integer NOT NULL,
    id_credit integer NOT NULL,
    lnr_date_deposit date NOT NULL,
    lnr_amount_payments money NOT NULL,
    lnr_contribution_status character varying(1) NOT NULL
);
 #   DROP TABLE public.loan_repayments;
       public         heap    postgres    false            �            1259    16605    loan_repayments_id_payout_seq    SEQUENCE     �   CREATE SEQUENCE public.loan_repayments_id_payout_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 4   DROP SEQUENCE public.loan_repayments_id_payout_seq;
       public          postgres    false    224            }           0    0    loan_repayments_id_payout_seq    SEQUENCE OWNED BY     _   ALTER SEQUENCE public.loan_repayments_id_payout_seq OWNED BY public.loan_repayments.id_payout;
          public          postgres    false    223            �            1259    16661    number    TABLE     =   CREATE TABLE public.number (
    numbers integer NOT NULL
);
    DROP TABLE public.number;
       public         heap    postgres    false            �            1259    16740    users    TABLE     �   CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(255) NOT NULL,
    role character varying(50) DEFAULT 'user'::character varying NOT NULL
);
    DROP TABLE public.users;
       public         heap    postgres    false            �            1259    16739    users_id_seq    SEQUENCE     �   CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.users_id_seq;
       public          postgres    false    227            ~           0    0    users_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;
          public          postgres    false    226            �           2604    16573    client id_client    DEFAULT     t   ALTER TABLE ONLY public.client ALTER COLUMN id_client SET DEFAULT nextval('public.client_id_client_seq'::regclass);
 ?   ALTER TABLE public.client ALTER COLUMN id_client DROP DEFAULT;
       public          postgres    false    215    216    216            �           2604    16581    credit id_credit    DEFAULT     t   ALTER TABLE ONLY public.credit ALTER COLUMN id_credit SET DEFAULT nextval('public.credit_id_credit_seq'::regclass);
 ?   ALTER TABLE public.credit ALTER COLUMN id_credit DROP DEFAULT;
       public          postgres    false    217    218    218            �           2604    16591     credit_history id_credit_history    DEFAULT     �   ALTER TABLE ONLY public.credit_history ALTER COLUMN id_credit_history SET DEFAULT nextval('public.credit_history_id_credit_history_seq'::regclass);
 O   ALTER TABLE public.credit_history ALTER COLUMN id_credit_history DROP DEFAULT;
       public          postgres    false    219    220    220            �           2604    16601 !   credit_products id_credit_product    DEFAULT     �   ALTER TABLE ONLY public.credit_products ALTER COLUMN id_credit_product SET DEFAULT nextval('public.credit_products_id_credit_product_seq'::regclass);
 P   ALTER TABLE public.credit_products ALTER COLUMN id_credit_product DROP DEFAULT;
       public          postgres    false    221    222    222            �           2604    16609    loan_repayments id_payout    DEFAULT     �   ALTER TABLE ONLY public.loan_repayments ALTER COLUMN id_payout SET DEFAULT nextval('public.loan_repayments_id_payout_seq'::regclass);
 H   ALTER TABLE public.loan_repayments ALTER COLUMN id_payout DROP DEFAULT;
       public          postgres    false    223    224    224            �           2604    16743    users id    DEFAULT     d   ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);
 7   ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    227    226    227            g          0    16570    client 
   TABLE DATA           �   COPY public.client (id_client, clt_last_name, clt_name, clt_middle_name, clt_date_birth, clt_residential_address, clt_income, clt_passport_data, clt_marital_status) FROM stdin;
    public          postgres    false    216   �e       i          0    16578    credit 
   TABLE DATA           �   COPY public.credit (id_credit, id_client, id_credit_product, crt_date_issue, crt_monthly_contributions, crt_maturity_date, crt_percent_on_credit, crt_status_credit, crt_sum_credit) FROM stdin;
    public          postgres    false    218   i       k          0    16588    credit_history 
   TABLE DATA           s   COPY public.credit_history (id_credit_history, id_client, id_credit, chs_amount_debt, chs_loan_status) FROM stdin;
    public          postgres    false    220   k       m          0    16598    credit_products 
   TABLE DATA           �   COPY public.credit_products (id_credit_product, cpr_name_product, cpr_min_koef, cpr_max_koef, cpr_min_date_return, cpr_max_date_return) FROM stdin;
    public          postgres    false    222   fk       o          0    16606    loan_repayments 
   TABLE DATA           �   COPY public.loan_repayments (id_payout, id_client, id_credit, lnr_date_deposit, lnr_amount_payments, lnr_contribution_status) FROM stdin;
    public          postgres    false    224   l       p          0    16661    number 
   TABLE DATA           )   COPY public.number (numbers) FROM stdin;
    public          postgres    false    225   �m       r          0    16740    users 
   TABLE DATA           =   COPY public.users (id, username, password, role) FROM stdin;
    public          postgres    false    227   �m                  0    0    client_id_client_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.client_id_client_seq', 52, true);
          public          postgres    false    215            �           0    0 $   credit_history_id_credit_history_seq    SEQUENCE SET     R   SELECT pg_catalog.setval('public.credit_history_id_credit_history_seq', 7, true);
          public          postgres    false    219            �           0    0    credit_id_credit_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.credit_id_credit_seq', 70, true);
          public          postgres    false    217            �           0    0 %   credit_products_id_credit_product_seq    SEQUENCE SET     S   SELECT pg_catalog.setval('public.credit_products_id_credit_product_seq', 8, true);
          public          postgres    false    221            �           0    0    loan_repayments_id_payout_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.loan_repayments_id_payout_seq', 57, true);
          public          postgres    false    223            �           0    0    users_id_seq    SEQUENCE SET     :   SELECT pg_catalog.setval('public.users_id_seq', 7, true);
          public          postgres    false    226            �           2606    16665    number number_pkey 
   CONSTRAINT     U   ALTER TABLE ONLY public.number
    ADD CONSTRAINT number_pkey PRIMARY KEY (numbers);
 <   ALTER TABLE ONLY public.number DROP CONSTRAINT number_pkey;
       public            postgres    false    225            �           2606    16575    client pk_client 
   CONSTRAINT     U   ALTER TABLE ONLY public.client
    ADD CONSTRAINT pk_client PRIMARY KEY (id_client);
 :   ALTER TABLE ONLY public.client DROP CONSTRAINT pk_client;
       public            postgres    false    216            �           2606    16583    credit pk_credit 
   CONSTRAINT     U   ALTER TABLE ONLY public.credit
    ADD CONSTRAINT pk_credit PRIMARY KEY (id_credit);
 :   ALTER TABLE ONLY public.credit DROP CONSTRAINT pk_credit;
       public            postgres    false    218            �           2606    16593     credit_history pk_credit_history 
   CONSTRAINT     m   ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT pk_credit_history PRIMARY KEY (id_credit_history);
 J   ALTER TABLE ONLY public.credit_history DROP CONSTRAINT pk_credit_history;
       public            postgres    false    220            �           2606    16603 "   credit_products pk_credit_products 
   CONSTRAINT     o   ALTER TABLE ONLY public.credit_products
    ADD CONSTRAINT pk_credit_products PRIMARY KEY (id_credit_product);
 L   ALTER TABLE ONLY public.credit_products DROP CONSTRAINT pk_credit_products;
       public            postgres    false    222            �           2606    16611 "   loan_repayments pk_loan_repayments 
   CONSTRAINT     g   ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT pk_loan_repayments PRIMARY KEY (id_payout);
 L   ALTER TABLE ONLY public.loan_repayments DROP CONSTRAINT pk_loan_repayments;
       public            postgres    false    224            �           2606    16746    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public            postgres    false    227            �           2606    16748    users users_username_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);
 B   ALTER TABLE ONLY public.users DROP CONSTRAINT users_username_key;
       public            postgres    false    227            �           1259    16576 	   client_pk    INDEX     H   CREATE UNIQUE INDEX client_pk ON public.client USING btree (id_client);
    DROP INDEX public.client_pk;
       public            postgres    false    216            �           1259    16594    credit_history_pk    INDEX     `   CREATE UNIQUE INDEX credit_history_pk ON public.credit_history USING btree (id_credit_history);
 %   DROP INDEX public.credit_history_pk;
       public            postgres    false    220            �           1259    16584 	   credit_pk    INDEX     H   CREATE UNIQUE INDEX credit_pk ON public.credit USING btree (id_credit);
    DROP INDEX public.credit_pk;
       public            postgres    false    218            �           1259    16604    credit_products_pk    INDEX     b   CREATE UNIQUE INDEX credit_products_pk ON public.credit_products USING btree (id_credit_product);
 &   DROP INDEX public.credit_products_pk;
       public            postgres    false    222            �           1259    16660    crt_date_issue    INDEX     K   CREATE INDEX crt_date_issue ON public.credit USING btree (crt_date_issue);
 "   DROP INDEX public.crt_date_issue;
       public            postgres    false    218            �           1259    16659    crt_sum_credit    INDEX     K   CREATE INDEX crt_sum_credit ON public.credit USING btree (crt_sum_credit);
 "   DROP INDEX public.crt_sum_credit;
       public            postgres    false    218            �           1259    16586    has_credit_products_fk    INDEX     V   CREATE INDEX has_credit_products_fk ON public.credit USING btree (id_credit_product);
 *   DROP INDEX public.has_credit_products_fk;
       public            postgres    false    218            �           1259    16595    has_history_fk    INDEX     N   CREATE INDEX has_history_fk ON public.credit_history USING btree (id_client);
 "   DROP INDEX public.has_history_fk;
       public            postgres    false    220            �           1259    16612    loan_repayments_pk    INDEX     Z   CREATE UNIQUE INDEX loan_repayments_pk ON public.loan_repayments USING btree (id_payout);
 &   DROP INDEX public.loan_repayments_pk;
       public            postgres    false    224            �           1259    16596    paid_fk    INDEX     G   CREATE INDEX paid_fk ON public.credit_history USING btree (id_credit);
    DROP INDEX public.paid_fk;
       public            postgres    false    220            �           1259    16614    payments_fk    INDEX     L   CREATE INDEX payments_fk ON public.loan_repayments USING btree (id_credit);
    DROP INDEX public.payments_fk;
       public            postgres    false    224            �           1259    16613    pays_out_fk    INDEX     L   CREATE INDEX pays_out_fk ON public.loan_repayments USING btree (id_client);
    DROP INDEX public.pays_out_fk;
       public            postgres    false    224            �           1259    16585 
   registr_fk    INDEX     B   CREATE INDEX registr_fk ON public.credit USING btree (id_client);
    DROP INDEX public.registr_fk;
       public            postgres    false    218            �           2620    16682 %   credit trigger_set_default_issue_date    TRIGGER     �   CREATE TRIGGER trigger_set_default_issue_date BEFORE INSERT ON public.credit FOR EACH ROW EXECUTE FUNCTION public.set_default_issue_date();
 >   DROP TRIGGER trigger_set_default_issue_date ON public.credit;
       public          postgres    false    228    218            �           2620    16692 4   loan_repayments trigger_set_default_repayment_amount    TRIGGER     �   CREATE TRIGGER trigger_set_default_repayment_amount BEFORE INSERT ON public.loan_repayments FOR EACH ROW EXECUTE FUNCTION public.set_default_repayment_amount();
 M   DROP TRIGGER trigger_set_default_repayment_amount ON public.loan_repayments;
       public          postgres    false    229    224            �           2620    16696     credit trigger_set_maturity_date    TRIGGER     �   CREATE TRIGGER trigger_set_maturity_date BEFORE INSERT ON public.credit FOR EACH ROW EXECUTE FUNCTION public.set_maturity_date_from_product();
 9   DROP TRIGGER trigger_set_maturity_date ON public.credit;
       public          postgres    false    218    230            �           2606    16625 +   credit_history fk_credit_h_has_histo_client    FK CONSTRAINT     �   ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT fk_credit_h_has_histo_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON UPDATE RESTRICT ON DELETE RESTRICT;
 U   ALTER TABLE ONLY public.credit_history DROP CONSTRAINT fk_credit_h_has_histo_client;
       public          postgres    false    3507    216    220            �           2606    16630 &   credit_history fk_credit_h_paid_credit    FK CONSTRAINT     �   ALTER TABLE ONLY public.credit_history
    ADD CONSTRAINT fk_credit_h_paid_credit FOREIGN KEY (id_credit) REFERENCES public.credit(id_credit) ON UPDATE RESTRICT ON DELETE RESTRICT;
 P   ALTER TABLE ONLY public.credit_history DROP CONSTRAINT fk_credit_h_paid_credit;
       public          postgres    false    3513    218    220            �           2606    16615 #   credit fk_credit_has_credi_credit_p    FK CONSTRAINT     �   ALTER TABLE ONLY public.credit
    ADD CONSTRAINT fk_credit_has_credi_credit_p FOREIGN KEY (id_credit_product) REFERENCES public.credit_products(id_credit_product) ON UPDATE RESTRICT ON DELETE RESTRICT;
 M   ALTER TABLE ONLY public.credit DROP CONSTRAINT fk_credit_has_credi_credit_p;
       public          postgres    false    3522    218    222            �           2606    16620    credit fk_credit_registr_client    FK CONSTRAINT     �   ALTER TABLE ONLY public.credit
    ADD CONSTRAINT fk_credit_registr_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON UPDATE RESTRICT ON DELETE RESTRICT;
 I   ALTER TABLE ONLY public.credit DROP CONSTRAINT fk_credit_registr_client;
       public          postgres    false    216    3507    218            �           2606    16635 +   loan_repayments fk_loan_rep_payments_credit    FK CONSTRAINT     �   ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT fk_loan_rep_payments_credit FOREIGN KEY (id_credit) REFERENCES public.credit(id_credit) ON UPDATE RESTRICT ON DELETE RESTRICT;
 U   ALTER TABLE ONLY public.loan_repayments DROP CONSTRAINT fk_loan_rep_payments_credit;
       public          postgres    false    224    218    3513            �           2606    16640 +   loan_repayments fk_loan_rep_pays_out_client    FK CONSTRAINT     �   ALTER TABLE ONLY public.loan_repayments
    ADD CONSTRAINT fk_loan_rep_pays_out_client FOREIGN KEY (id_client) REFERENCES public.client(id_client) ON UPDATE RESTRICT ON DELETE RESTRICT;
 U   ALTER TABLE ONLY public.loan_repayments DROP CONSTRAINT fk_loan_rep_pays_out_client;
       public          postgres    false    216    3507    224            g     x����n�@������n�����#�����N�H+
�J (*�� YM�&m������f���Ɩ*D�����o�|3�]м<,�҆��B�gZ�MyH��Z��Q*�J�+h:��8r���t#�D�)����$c�?BGG��K�+�7��Fy"�C�{K�k�vY.��&��Gt��[sZc{M��(��b�M��	i�Ｇ���9M��
4{�"�o,�x��~N��V�D�T���G�#_��`���ϱ�)'0_	���e��f�Dk�T��nȓ�����j?��M��<�7rA���J3
&��n�A��4�Re�$*@"��@��D�ik{��� �v���*²�&U%�oQ~�9�>|D�������A��9�S,��o��r2QC.\��l�F��&�6� ZAg��F�����*y儽�\�X��_I�>�C~�����~��qp�9������_���[!�|�M�Q�D����i( k�I�ɽ�#y���_��gH3؅���	`�	|�t�oM�F��ϐpL��^���̼
�3W��?>���?<�cUyt�{T7Brb�>u�a�U�7U}�)���|��1��}�b�Mè��������=�^�>x��Ͱ�}l��V2�V>Y��MG�n���*�\������ݍi�_}I2�W��7*;�������޾��'T3��(H2�cƸ���#��HG�!g�Ou�O�8wVX��VL���>3����6��r���N�x��d?����gk�      i   �  x���[��0E��:�i� 	�������N�g��S� _@ �\?��!�教���?<��d]$\uk��%eIi��E7��i$�Q�7x�R6T�ݓ��.�,u������B�6B}�!F���]�\<�hiq�T�S0��:���
��у,j�jUX@ߜ,��Mc$q�z(w�Y&��ҝ卓��a�Y��aWӇl$#<������`��k �c斚Xq��;��$��bC�V�G���A� �0^���e���B�g�..d2��w�e���G���Ȗq�)�gM�������7 �OU�ܜ+�w�(M�,E:KQ����zxc��ta3�7���b�w��oZ����˔��{�|���!�|��2%G�q5N턷��6;�*v�Pٗ����yP��&h���h%���� ���u��}cz��7��������H��㉾�]?$���D�sS����}�b�Y6�}Y��j��n��m����a�U�-���f����ϥ"�˲���_�      k   D   x�Eʱ	�0C�Z7Ǖ�Hg�Y&���j���j/�F��`��Cc7u!Ǳ�ƕ��b������x́9      m   �   x�m���0D��]�~l,eZ& @DIAI#��H!Q�
�8cH������r�	L�B��h��#�b��y(�K�X��'�aK�.T�P��u�s�sLy!׈��!���"5s�����\�,�a��5F��&4���v��(�\o���]�~��Ҭ2c�Ɨe�      o   g  x���Ir�@E��^�.�����#�"K�Iy��{���ه��I�D�㎈/D���D�b��(+X�]=1Uǋ/�T^Aa|�
�0Z�M��t@�zwf;��fWB�l'�1g�0�l.v&���j��HN�����x��s�����Ck����i���%q\��K�xM������[�#��9a�!?J�iȏR~ţ�x�;_)�R�у!cC����0(uap0�`���x���F-��)-2e����'Cݢü�VU�����E�߸�
�H۞���x/���V^c�
O,^�M��8��q�5N�_�<�//��p��^'�{�.Z��m���8���?g�zm����j      p   '   x�34�24�24���2�2�2�2�2��r��qqq H"$      r   q  x�e�AO�1�s�;zF��8Io0��إ��i�q$��X�2���Ka7N�9y�7�z[�Z�x~=m	��mݦ͗��]�_��o�����ft�̅�j��S������Dհ4q콳��Ѭ�aZF�A�Q(�L�!%@'�ʘͩ�:iE�A���j�H��uZiy:|��w�~���=��ݽ>l�#}\�������xh���L�k!Rk�
�Ebp��j�V�U�����p�^�I�"�3�t���5_����u���q������t�9<��޴����m�txe�.�i��,�fi�mn)�&έ����
һ[1(X�{/C�<+�:�nl�y�LL��Y��%�3�N���/���Z��� U6��     