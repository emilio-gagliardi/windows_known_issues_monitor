--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

-- Started on 2024-07-04 12:22:27

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 16435)
-- Name: changes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.changes (
    id integer NOT NULL,
    scrape_id integer,
    change_type character varying,
    details character varying
);


ALTER TABLE public.changes OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16434)
-- Name: changes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.changes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.changes_id_seq OWNER TO postgres;

--
-- TOC entry 4867 (class 0 OID 0)
-- Dependencies: 219
-- Name: changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.changes_id_seq OWNED BY public.changes.id;


--
-- TOC entry 218 (class 1259 OID 16420)
-- Name: scrapes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scrapes (
    id integer NOT NULL,
    url_id integer,
    "timestamp" timestamp without time zone,
    content character varying,
    scrape_type character varying,
    scrape_comment character varying,
    create_alert boolean,
    hash character varying(32)
);


ALTER TABLE public.scrapes OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16419)
-- Name: scrapes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scrapes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scrapes_id_seq OWNER TO postgres;

--
-- TOC entry 4868 (class 0 OID 0)
-- Dependencies: 217
-- Name: scrapes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scrapes_id_seq OWNED BY public.scrapes.id;


--
-- TOC entry 216 (class 1259 OID 16409)
-- Name: urls; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.urls (
    id integer NOT NULL,
    url character varying,
    last_scraped date
);


ALTER TABLE public.urls OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 16408)
-- Name: urls_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.urls_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urls_id_seq OWNER TO postgres;

--
-- TOC entry 4869 (class 0 OID 0)
-- Dependencies: 215
-- Name: urls_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.urls_id_seq OWNED BY public.urls.id;


--
-- TOC entry 4700 (class 2604 OID 16438)
-- Name: changes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.changes ALTER COLUMN id SET DEFAULT nextval('public.changes_id_seq'::regclass);


--
-- TOC entry 4699 (class 2604 OID 16423)
-- Name: scrapes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scrapes ALTER COLUMN id SET DEFAULT nextval('public.scrapes_id_seq'::regclass);


--
-- TOC entry 4698 (class 2604 OID 16412)
-- Name: urls id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls ALTER COLUMN id SET DEFAULT nextval('public.urls_id_seq'::regclass);


--
-- TOC entry 4861 (class 0 OID 16435)
-- Dependencies: 220
-- Data for Name: changes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.changes (id, scrape_id, change_type, details) FROM stdin;
\.


--
-- TOC entry 4859 (class 0 OID 16420)
-- Dependencies: 218
-- Data for Name: scrapes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.scrapes (id, url_id, "timestamp", content, scrape_type, scrape_comment, create_alert, hash) FROM stdin;
184	1	2024-07-01 19:45:07.772451	{"known_issues": {"header": "Known issues", "row": {"Summary": "The June non-security preview update might cause devices to restart repeatedlyThis issue is more likely to affect devices utilizing virtual machines and nested virtualization features", "Originating update": "OS Build 22621.3810 | KB5039302 | 2024-06-25", "Status": "Confirmed", "Last updated": "2024-06-28 15:06 PT"}}}	\N	\N	f	b1d2583a14f06a6fa888b30a99f74fc2
185	1	2024-07-01 19:45:07.778458	{"known_issues": {"header": "Known issues", "row": {"Summary": "Taskbar might not load after installing the June 2024 preview updateThis issue is only expected to occur in Windows N editions or if the \\u2018Media Features\\u2019 is turned off in Windows Features", "Originating update": "OS Build 22621.3810 | KB5039302 | 2024-06-25", "Status": "Confirmed", "Last updated": "2024-06-28 13:33 PT"}}}	\N	\N	f	8a71eacca7adac8bd1b35476ce4745a0
186	1	2024-07-01 19:45:07.784461	{"known_issues": {"header": "Known issues", "row": {"Summary": "Photos app might fail to start when BlockNonAdminUserInstall is enabledThis issue might be observed after device updates the Photos app to version 2024.11050.29009.0 from the Microsoft store", "Originating update": "N/A", "Status": "Confirmed", "Last updated": "2024-06-18 10:29 PT"}}}	\N	\N	f	15427e98302039ac2676c3566db36389
187	1	2024-07-01 19:45:07.790989	{"known_issues": {"header": "Known issues", "row": {"Summary": "Edge updates might cause Microsoft Copilot app to show up in Installed appsEdge updates might install a new package and users might see Microsoft Copilot app among the device's Installed apps", "Originating update": "N/A", "Status": "Resolved", "Last updated": "2024-06-13 14:21 PT"}}}	\N	\N	f	225a4704bb96a0f6aa5fb80c97726f55
188	2	2024-07-01 19:45:09.275253	{"known_issues": {"header": "Known issues", "row": {"Summary": "The June non-security preview update might cause devices to restart repeatedlyThis issue is more likely to affect devices utilizing virtual machines and nested virtualization features", "Originating update": "OS Build 22621.3810 | KB5039302 | 2024-06-25", "Status": "Confirmed", "Last updated": "2024-06-28 15:06 PT"}}}	\N	\N	f	b1d2583a14f06a6fa888b30a99f74fc2
189	2	2024-07-01 19:45:09.282265	{"known_issues": {"header": "Known issues", "row": {"Summary": "Taskbar might not load after installing the June 2024 preview updateThis issue is only expected to occur in Windows N editions or if the \\u2018Media Features\\u2019 is turned off in Windows Features", "Originating update": "OS Build 22621.3810 | KB5039302 | 2024-06-25", "Status": "Confirmed", "Last updated": "2024-06-28 13:33 PT"}}}	\N	\N	f	8a71eacca7adac8bd1b35476ce4745a0
190	2	2024-07-01 19:45:09.287768	{"known_issues": {"header": "Known issues", "row": {"Summary": "Photos app might fail to start when BlockNonAdminUserInstall is enabledThis issue might be observed after device updates the Photos app to version 2024.11050.29009.0 from the Microsoft store", "Originating update": "N/A", "Status": "Confirmed", "Last updated": "2024-06-18 10:29 PT"}}}	\N	\N	f	15427e98302039ac2676c3566db36389
191	2	2024-07-01 19:45:09.293786	{"known_issues": {"header": "Known issues", "row": {"Summary": "Edge updates might cause Microsoft Copilot app to show up in Installed appsEdge updates might install a new package and users might see Microsoft Copilot app among the device's Installed apps", "Originating update": "N/A", "Status": "Resolved", "Last updated": "2024-06-13 14:21 PT"}}}	\N	\N	f	225a4704bb96a0f6aa5fb80c97726f55
192	3	2024-07-01 19:45:10.738371	{"known_issues": {"header": "Known issues", "row": {"Summary": "Edge updates might cause Microsoft Copilot app to show up in Installed appsEdge updates might install a new package and users might see Microsoft Copilot app among the device's Installed apps", "Originating update": "N/A", "Status": "Resolved", "Last updated": "2024-06-13 14:21 PT"}}}	\N	\N	f	225a4704bb96a0f6aa5fb80c97726f55
193	3	2024-07-01 19:45:10.745014	{"known_issues": {"header": "Known issues", "row": {"Summary": "BitLocker might incorrectly receive a 65000 error in MDMs\\"Requires Device Encryption\\" might incorrectly report as an error in some managed environments.", "Originating update": "N/A", "Status": "Resolved KB5039213", "Last updated": "2024-06-11 10:02 PT"}}}	\N	\N	f	56336745b0c70d4f60c55b6485eb4f36
194	3	2024-07-01 19:45:10.750044	{"known_issues": {"header": "Known issues", "row": {"Summary": "Devices with locale set to Croatia might not utilize the expected currencyThis can affect applications which retrieve the device's currency for purchases or other transactions", "Originating update": "N/A", "Status": "Confirmed", "Last updated": "2023-10-31 10:06 PT"}}}	\N	\N	f	f9686ec4b324576efd12fc0d05d0166f
195	4	2024-07-01 19:45:12.716612	{"known_issues": {"header": "Known issues", "row": {"Summary": "Desktop icons might move unexpectedly between monitorsThis issue is only observed if you are using more than one monitor when attempting to use Copilot in Windows.", "Originating update": "OS Build 19045.3758 | KB5032278 | 2023-11-30", "Status": "Resolved", "Last updated": "2024-06-28 15:28 PT"}}}	\N	\N	f	df8106d365e98bf106ed27738abfe259
196	4	2024-07-01 19:45:12.720119	{"known_issues": {"header": "Known issues", "row": {"Summary": "Apps show \\"Open With\\" dialog when right-clicking on Taskbar or Start menu iconsYou might experience this when right-clicking an app icon shown in your Taskbar or Start menu to execute a task.", "Originating update": "OS Build 19045.4355 | KB5036979 | 2024-04-23", "Status": "Resolved", "Last updated": "2024-06-25 14:02 PT"}}}	\N	\N	f	b6862ede32f7212821b1f7b9501e7e6e
197	4	2024-07-01 19:45:12.726633	{"known_issues": {"header": "Known issues", "row": {"Summary": "Edge updates might cause Microsoft Copilot app to show up in Installed appsEdge updates might install a new package and users might see Microsoft Copilot app among the device's Installed apps", "Originating update": "N/A", "Status": "Resolved", "Last updated": "2024-06-13 14:21 PT"}}}	\N	\N	f	225a4704bb96a0f6aa5fb80c97726f55
198	4	2024-07-01 19:45:12.73315	{"known_issues": {"header": "Known issues", "row": {"Summary": "Enterprise customers might be unable to use Microsoft Connected CacheThis issue affects Windows devices which use the DHCP Option 235 to configure the Microsoft Connected Cache endpoint", "Originating update": "OS Build 19045.3996 | KB5034203 | 2024-01-23", "Status": "Mitigated", "Last updated": "2024-04-05 11:43 PT"}}}	\N	\N	f	91f3d821e0b5c4c287d821b0b8782db9
199	4	2024-07-01 19:45:12.739174	{"known_issues": {"header": "Known issues", "row": {"Summary": "Devices with locale set to Croatia might not utilize the expected currencyThis can affect applications which retrieve the device's currency for purchases or other transactions", "Originating update": "N/A", "Status": "Confirmed", "Last updated": "2023-10-31 10:06 PT"}}}	\N	\N	f	f9686ec4b324576efd12fc0d05d0166f
200	6	2024-07-01 19:45:14.280664	{"known_issues": {"header": "Known issues", "row": {"Summary": "Synapse SQL Serverless Pool databases go on \\"Recovery pending\\" stateIssue affects cloud-based SQL servers with the Windows June 2024 security update installed", "Originating update": "OS Build 20348.2527 | KB5039227 | 2024-06-11", "Status": "Resolved KB5041054", "Last updated": "2024-06-20 17:08 PT"}}}	\N	\N	f	6de3fdc02218910d9abaa079fd13f7c2
201	6	2024-07-01 19:45:14.285667	{"known_issues": {"header": "Known issues", "row": {"Summary": "Edge updates might cause Microsoft Copilot app to show up in Installed appsEdge updates might install a new package and users might see Microsoft Copilot app among the device's Installed apps", "Originating update": "N/A", "Status": "Resolved", "Last updated": "2024-06-13 14:21 PT"}}}	\N	\N	f	225a4704bb96a0f6aa5fb80c97726f55
202	6	2024-07-01 19:45:14.293247	{"known_issues": {"header": "Known issues", "row": {"Summary": "Certain apps or devices might be unable to create Netlogon secure channel connectionsScenarios which rely on synthetic RODC machine accounts might fail if they do not have a linked KRBTGT account.", "Originating update": "OS Build 20348.469 | KB5009555 | 2022-01-11", "Status": "Investigating", "Last updated": "2022-02-24 17:41 PT"}}}	\N	\N	f	7936f365d0bc5054578b36ef6a7a596b
203	6	2024-07-01 19:45:14.299717	{"known_issues": {"header": "Known issues", "row": {"Summary": "Apps that acquire or set Active Directory Forest Trust Information might have issuesApps using Microsoft .NET to acquire or set Forest Trust Information might fail, close, or you might receive an error.", "Originating update": "OS Build 20348.469 | KB5009555 | 2022-01-11", "Status": "Mitigated", "Last updated": "2022-02-07 15:36 PT"}}}	\N	\N	f	a088503516a3b123d0ae87d9f1a42f36
205	5	2024-07-01 19:45:15.8906	{"known_issues": {"header": "Known issues", "row": {"Summary": "Enterprise customers might be unable to use Microsoft Connected CacheThis issue affects Windows devices which use the DHCP Option 235 to configure the Microsoft Connected Cache endpoint", "Originating update": "OS Build 19044.4046 | KB5034763 | 2024-02-13", "Status": "Mitigated", "Last updated": "2024-04-05 11:43 PT"}}}	\N	\N	f	0d648ef173f0f4f8ca6f4d8270d4cdf6
206	5	2024-07-01 19:45:15.898123	{"known_issues": {"header": "Known issues", "row": {"Summary": "Devices with locale set to Croatia might not utilize the expected currencyThis can affect applications which retrieve the device's currency for purchases or other transactions", "Originating update": "N/A", "Status": "Confirmed", "Last updated": "2023-10-31 10:06 PT"}}}	\N	\N	f	f9686ec4b324576efd12fc0d05d0166f
207	5	2024-07-03 10:55:47.165526	{"known_issues": {"header": "Known issues", "row": {"Summary": "Apps show \\"Open With\\" dialog when right-clicking on Taskbar or Start menu iconsYou might experience this when right-clicking an app icon shown in your Taskbar or Start menu to execute a task.", "Originating update": "OS Build 19044.4412 | KB5037768 | 2024-05-14", "Status": "Confirmed", "Last updated": "2024-06-17 09:58 PT"}}}	\N	\N	f	b8a9fcaff4f9c5678b9afe3ad61d92c8
\.


--
-- TOC entry 4857 (class 0 OID 16409)
-- Dependencies: 216
-- Data for Name: urls; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.urls (id, url, last_scraped) FROM stdin;
1	https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-23H2	2024-07-01
2	https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-22H2	2024-07-01
3	https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-21H2	2024-07-01
4	https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-22H2	2024-07-01
6	https://learn.microsoft.com/en-us/windows/release-health/status-windows-server-2022	2024-07-01
5	https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2	2024-07-03
\.


--
-- TOC entry 4870 (class 0 OID 0)
-- Dependencies: 219
-- Name: changes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.changes_id_seq', 1, false);


--
-- TOC entry 4871 (class 0 OID 0)
-- Dependencies: 217
-- Name: scrapes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.scrapes_id_seq', 207, true);


--
-- TOC entry 4872 (class 0 OID 0)
-- Dependencies: 215
-- Name: urls_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.urls_id_seq', 17, true);


--
-- TOC entry 4709 (class 2606 OID 16442)
-- Name: changes changes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.changes
    ADD CONSTRAINT changes_pkey PRIMARY KEY (id);


--
-- TOC entry 4707 (class 2606 OID 16427)
-- Name: scrapes scrapes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scrapes
    ADD CONSTRAINT scrapes_pkey PRIMARY KEY (id);


--
-- TOC entry 4704 (class 2606 OID 16416)
-- Name: urls urls_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT urls_pkey PRIMARY KEY (id);


--
-- TOC entry 4710 (class 1259 OID 16448)
-- Name: ix_changes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_changes_id ON public.changes USING btree (id);


--
-- TOC entry 4705 (class 1259 OID 16433)
-- Name: ix_scrapes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scrapes_id ON public.scrapes USING btree (id);


--
-- TOC entry 4701 (class 1259 OID 16418)
-- Name: ix_urls_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_urls_id ON public.urls USING btree (id);


--
-- TOC entry 4702 (class 1259 OID 16417)
-- Name: ix_urls_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_urls_url ON public.urls USING btree (url);


--
-- TOC entry 4712 (class 2606 OID 16443)
-- Name: changes changes_scrape_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.changes
    ADD CONSTRAINT changes_scrape_id_fkey FOREIGN KEY (scrape_id) REFERENCES public.scrapes(id);


--
-- TOC entry 4711 (class 2606 OID 16428)
-- Name: scrapes scrapes_url_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scrapes
    ADD CONSTRAINT scrapes_url_id_fkey FOREIGN KEY (url_id) REFERENCES public.urls(id);


-- Completed on 2024-07-04 12:22:27

--
-- PostgreSQL database dump complete
--

