-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler version: 0.9.4
-- PostgreSQL version: 13.0
-- Project Site: pgmodeler.io
-- Model Author: ---
-- object: flower_care | type: ROLE --
-- DROP ROLE IF EXISTS flower_care;
CREATE ROLE flower_care WITH 
	LOGIN
	UNENCRYPTED PASSWORD '!flower!care!';
-- ddl-end --
COMMENT ON ROLE flower_care IS E'Utilisateur de la base.';
-- ddl-end --


-- Database creation must be performed outside a multi lined SQL file. 
-- These commands were put in this file only as a convenience.
-- 
-- object: flower_care | type: DATABASE --
-- DROP DATABASE IF EXISTS flower_care;
CREATE DATABASE flower_care;
-- ddl-end --
\c flower_care

-- object: public.data | type: TABLE --
-- DROP TABLE IF EXISTS public.data CASCADE;
CREATE TABLE public.data (
	device char(17) NOT NULL,
	"timestamp" timestamp NOT NULL,
	temperature numeric(3,1),
	moisture smallint,
	light smallint,
	conductivity smallint,
	id_garden smallint NOT NULL,
	CONSTRAINT "primary" PRIMARY KEY (device,"timestamp")
);
-- ddl-end --
COMMENT ON TABLE public.data IS E'Données des capteurs météo';
-- ddl-end --
COMMENT ON COLUMN public.data.device IS E'L''adresse mac du capteur. Au format hex:hex...\nex : 5c:85:7e:b0:0d:0b';
-- ddl-end --
COMMENT ON COLUMN public.data."timestamp" IS E'La date et l''heure du relevé. On arrondit aux heures.';
-- ddl-end --
COMMENT ON COLUMN public.data.temperature IS E'En degré Celsius';
-- ddl-end --
COMMENT ON COLUMN public.data.moisture IS E'Humidité du sol en %.';
-- ddl-end --
COMMENT ON COLUMN public.data.light IS E'Luminosité en lux.';
-- ddl-end --
COMMENT ON COLUMN public.data.conductivity IS E'Conductivité (pour mesurer la fertilité du sol) en micro Siemens / cm.';
-- ddl-end --
ALTER TABLE public.data OWNER TO flower_care;
-- ddl-end --

-- object: public.garden | type: TABLE --
-- DROP TABLE IF EXISTS public.garden CASCADE;
CREATE TABLE public.garden (
	id smallint NOT NULL,
	name character varying(255),
	device smallint,
	CONSTRAINT garden_pk PRIMARY KEY (id)
);
-- ddl-end --
COMMENT ON TABLE public.garden IS E'Idenitfie un jardin et un capteur. \nSi on change le capteur, on met à jour la colonne device.';
-- ddl-end --
COMMENT ON COLUMN public.garden.name IS E'Nom du jardin';
-- ddl-end --
COMMENT ON COLUMN public.garden.device IS E'Adresse mac du capteur';
-- ddl-end --
ALTER TABLE public.garden OWNER TO flower_care;
-- ddl-end --

-- object: garden_fk | type: CONSTRAINT --
-- ALTER TABLE public.data DROP CONSTRAINT IF EXISTS garden_fk CASCADE;
ALTER TABLE public.data ADD CONSTRAINT garden_fk FOREIGN KEY (id_garden)
REFERENCES public.garden (id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --


