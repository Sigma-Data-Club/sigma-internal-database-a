

-- Tabla MIEMBRO
-- columna 'cargo' en restricciones
CREATE TABLE miembro (
    dni VARCHAR(10) PRIMARY KEY, -- Usamos VARCHAR para evitar problemas de espacios
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(50) UNIQUE NOT NULL,
    carrera VARCHAR(50), 
    curso VARCHAR(20) CHECK (curso IN ('1', '2', '3', '4', '5')),
    tlf VARCHAR(15),
    cargo VARCHAR(20) DEFAULT 'Socio' CHECK (cargo IN ('Presidente', 'Vicepresidente'))
);

-- Restricción solo un presidente
CREATE UNIQUE INDEX only_one_president ON miembro (cargo) WHERE cargo = 'Presidente';


-- Tabla EVENTO
CREATE TABLE evento (
    id_evento SERIAL PRIMARY KEY, -- SERIAL crea un autoincremental (1, 2, 3...)
    nombre VARCHAR(100) NOT NULL,
    fecha_evento DATE NOT NULL,
    aula VARCHAR(30),
    categoria VARCHAR(50),
    aforo INTEGER NOT NULL,
    premio VARCHAR(100),
    catering BOOLEAN DEFAULT FALSE,
    fecha_hora_pub TIMESTAMP NOT NULL,
    fecha_hora_sold_out TIMESTAMP,
    
    -- Restricción sold_out debe ser posterior a publicación
    CONSTRAINT check_fechas_soldout CHECK (fecha_hora_sold_out > fecha_hora_pub)
);


-- 4. Tabla EMPRESAS_PONENTES
CREATE TABLE empresas_ponentes (
    id_ponente SERIAL PRIMARY KEY,
    nombre_ponente VARCHAR(100) NOT NULL,
    empresa VARCHAR(100) NOT NULL,
    cargo VARCHAR(100)
);


-- Tabla PROYECTO
CREATE TABLE proyecto (
    id_proyecto SERIAL PRIMARY KEY,
    nombre_proy VARCHAR(100) NOT NULL,
    descripcion TEXT, 
    fecha_inicio DATE,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente', 'en proceso', 'finalizado'))
);


-- Tabla EVENTO_PONENTE (R N:M)
CREATE TABLE evento_ponente (
    id_evento INTEGER,
    id_ponente INTEGER,
    PRIMARY KEY (id_evento, id_ponente),
    
    FOREIGN KEY (id_evento) REFERENCES evento(id_evento) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    FOREIGN KEY (id_ponente) REFERENCES empresas_ponentes(id_ponente) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);


-- Tabla INSCRIPCIONES_EVENTOS
CREATE TABLE inscripciones_eventos (
    id_miembro VARCHAR(10),
    id_evento INTEGER,
    fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asistencia BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_miembro, id_evento),
    
    FOREIGN KEY (id_miembro) REFERENCES miembro(dni) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    FOREIGN KEY (id_evento) REFERENCES evento(id_evento) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);


-- Tabla PARTICIPACION_PROYECTOS
CREATE TABLE participacion_proyectos (
    id_miembro VARCHAR(10),
    id_proyecto INTEGER,
    rol VARCHAR(50),
    PRIMARY KEY (id_miembro, id_proyecto),
    
    FOREIGN KEY (id_miembro) REFERENCES miembro(dni) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);


-- Tabla PUBLICACION
CREATE TABLE publicacion (
    url_post VARCHAR(255) PRIMARY KEY,
    plataforma VARCHAR(30) NOT NULL,
    fecha_post TIMESTAMP NOT NULL,
    id_evento INTEGER,
    miembro_que_publico VARCHAR(10) NOT NULL,
    
    -- Si se borra el evento, se pone a NULL (la publicación queda huérfana pero existe)
    FOREIGN KEY (id_evento) REFERENCES evento(id_evento) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    -- Si se intenta borrar al miembro, ERROR (restrictivo)
    FOREIGN KEY (miembro_que_publico) REFERENCES miembro(dni) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);


-- Tabla METRICAS_RRSS
CREATE TABLE metricas_rrss (
    id_metrica SERIAL PRIMARY KEY,
    url_post VARCHAR(255) NOT NULL,
    fecha_medicion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    comentarios INTEGER DEFAULT 0,
    guardados INTEGER DEFAULT 0,
    
    FOREIGN KEY (url_post) REFERENCES publicacion(url_post) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);
