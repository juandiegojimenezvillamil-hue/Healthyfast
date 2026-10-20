-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 11-09-2026 a las 00:10:04
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `healthdb1`
--
CREATE DATABASE IF NOT EXISTS `healthdb1` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `healthdb1`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categorias`
--

DROP TABLE IF EXISTS `categorias`;
CREATE TABLE IF NOT EXISTS `categorias` (
  `id_categoria` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `categorias`
--

INSERT INTO `categorias` (`id_categoria`, `nombre`) VALUES
(1, 'Bebidas Saludables'),
(2, 'Snacks Orgánicos'),
(3, 'Suplementos'),
(4, 'Frutos Secos'),
(5, 'Proteínas'),
(6, 'Skincare'),
(7, 'Body Care'),
(8, 'Emergency'),
(9, 'Pets'),
(10, 'Botiquín');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `clientes`
--

DROP TABLE IF EXISTS `clientes`;
CREATE TABLE IF NOT EXISTS `clientes` (
  `id_cliente` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`),
  KEY `fk_clientes_usuario` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `clientes`
--

INSERT INTO `clientes` (`id_cliente`, `id_usuario`, `nombre`, `telefono`, `correo`) VALUES
(1, 6, 'Laura Cliente', '3001234567', 'cliente@healthyfast.com'),
(2, 7, 'Pedro Comprador', '3007654321', 'pedro.cliente@healthyfast.com'),
(3, 8, 'Ana Compradora', '3009876543', 'ana.cliente@healthyfast.com'),
(4, NULL, 'Estudiante Prueba', '3009998877', 'comprador@test.com');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `despachos`
--

DROP TABLE IF EXISTS `despachos`;
CREATE TABLE IF NOT EXISTS `despachos` (
  `id_despacho` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) DEFAULT NULL,
  `id_repartidor` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  PRIMARY KEY (`id_despacho`),
  KEY `fk_despachos_pedido` (`id_pedido`),
  KEY `fk_despachos_repartidor` (`id_repartidor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_movimiento`
--

DROP TABLE IF EXISTS `detalle_movimiento`;
CREATE TABLE IF NOT EXISTS `detalle_movimiento` (
  `id_detalle` int(11) NOT NULL AUTO_INCREMENT,
  `id_movimiento` int(11) DEFAULT NULL,
  `id_producto` int(11) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_detalle`),
  KEY `fk_detmov_movimiento` (`id_movimiento`),
  KEY `fk_detmov_producto` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_pedido`
--

DROP TABLE IF EXISTS `detalle_pedido`;
CREATE TABLE IF NOT EXISTS `detalle_pedido` (
  `id_detalle_pedido` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) DEFAULT NULL,
  `id_producto` int(11) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_detalle_pedido`),
  KEY `fk_detped_pedido` (`id_pedido`),
  KEY `fk_detped_producto` (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalle_pedido`
--

INSERT INTO `detalle_pedido` (`id_detalle_pedido`, `id_pedido`, `id_producto`, `cantidad`, `precio`) VALUES
(1, 1, 1, 1, 180000.00),
(2, 1, 2, 2, 120000.00),
(3, 2, 1, 1, 180000.00),
(4, 2, 2, 2, 120000.00),
(5, 3, 1, 1, 180000.00),
(6, 3, 2, 2, 120000.00),
(7, 4, 1, 1, 180000.00),
(8, 4, 2, 2, 120000.00),
(9, 5, 1, 1, 180000.00),
(10, 5, 2, 2, 120000.00),
(11, 6, 1, 1, 4500.00),
(12, 6, 2, 2, 2500.00),
(13, 7, 1, 1, 4500.00),
(14, 7, 2, 2, 2500.00),
(15, 8, 1, 1, 4500.00),
(16, 8, 2, 2, 2500.00),
(17, 9, 1, 1, 4500.00),
(18, 9, 2, 2, 2500.00),
(19, 10, 1, 1, 4500.00),
(20, 10, 2, 2, 2500.00),
(21, 11, 1, 1, 4500.00),
(22, 11, 2, 2, 2500.00),
(23, 12, 1, 1, 4500.00),
(24, 12, 2, 2, 2500.00),
(25, 13, 1, 1, 4500.00),
(26, 13, 2, 2, 2500.00),
(27, 14, 1, 1, 4500.00),
(28, 14, 2, 2, 2500.00),
(29, 15, 1, 1, 4500.00),
(30, 15, 2, 2, 2500.00),
(31, 16, 1, 1, 4500.00),
(32, 16, 2, 2, 2500.00),
(33, 17, 1, 1, 4500.00),
(34, 17, 2, 2, 2500.00),
(35, 18, 6, 1, 8900.00),
(36, 18, 7, 1, 95000.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `devoluciones`
--

DROP TABLE IF EXISTS `devoluciones`;
CREATE TABLE IF NOT EXISTS `devoluciones` (
  `id_devolucion` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_devolucion`),
  KEY `fk_devoluciones_pedido` (`id_pedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empleados`
--

DROP TABLE IF EXISTS `empleados`;
CREATE TABLE IF NOT EXISTS `empleados` (
  `id_empleado` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `cargo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_empleado`),
  KEY `fk_empleados_usuario` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `empleados`
--

INSERT INTO `empleados` (`id_empleado`, `id_usuario`, `nombre`, `cargo`) VALUES
(1, 3, 'Carlos Empleado', 'Vendedor'),
(2, 4, 'Marta Bodega', 'Encargada de Inventario'),
(3, 5, 'Jorge Caja', 'Cajero');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `facturas`
--

DROP TABLE IF EXISTS `facturas`;
CREATE TABLE IF NOT EXISTS `facturas` (
  `id_factura` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_factura`),
  KEY `fk_facturas_pedido` (`id_pedido`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `facturas`
--

INSERT INTO `facturas` (`id_factura`, `id_pedido`, `fecha`, `total`) VALUES
(1, 2, '2026-09-10', 420000.00),
(2, 3, '2026-09-10', 420000.00),
(3, 4, '2026-09-10', 420000.00),
(4, 5, '2026-09-10', 420000.00),
(5, 6, '2026-09-10', 9500.00),
(6, 7, '2026-09-10', 9500.00),
(7, 8, '2026-09-10', 9500.00),
(8, 9, '2026-09-10', 9500.00),
(9, 10, '2026-09-10', 9500.00),
(10, 11, '2026-09-10', 9500.00),
(11, 12, '2026-09-10', 9500.00),
(12, 13, '2026-09-10', 9500.00),
(13, 14, '2026-09-10', 9500.00),
(14, 15, '2026-09-10', 9500.00),
(15, 16, '2026-09-10', 9500.00),
(16, 17, '2026-09-10', 9500.00),
(17, 18, '2026-09-10', 103900.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimientos_inventario`
--

DROP TABLE IF EXISTS `movimientos_inventario`;
CREATE TABLE IF NOT EXISTS `movimientos_inventario` (
  `id_movimiento` int(11) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `fecha` date NOT NULL,
  PRIMARY KEY (`id_movimiento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos`
--

DROP TABLE IF EXISTS `pagos`;
CREATE TABLE IF NOT EXISTS `pagos` (
  `id_pago` int(11) NOT NULL AUTO_INCREMENT,
  `id_factura` int(11) DEFAULT NULL,
  `monto` decimal(10,2) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  PRIMARY KEY (`id_pago`),
  KEY `fk_pagos_factura` (`id_factura`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pagos`
--

INSERT INTO `pagos` (`id_pago`, `id_factura`, `monto`, `fecha`) VALUES
(1, 1, 420000.00, '2026-09-10'),
(2, 2, 420000.00, '2026-09-10'),
(3, 3, 420000.00, '2026-09-10'),
(4, 4, 420000.00, '2026-09-10'),
(5, 5, 9500.00, '2026-09-10'),
(6, 6, 9500.00, '2026-09-10'),
(7, 7, 9500.00, '2026-09-10'),
(8, 8, 9500.00, '2026-09-10'),
(9, 9, 9500.00, '2026-09-10'),
(10, 10, 9500.00, '2026-09-10'),
(11, 11, 9500.00, '2026-09-10'),
(12, 12, 9500.00, '2026-09-10'),
(13, 13, 9500.00, '2026-09-10'),
(14, 14, 9500.00, '2026-09-10'),
(15, 15, 9500.00, '2026-09-10'),
(16, 16, 9500.00, '2026-09-10'),
(17, 17, 103900.00, '2026-09-10');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pedidos`
--

DROP TABLE IF EXISTS `pedidos`;
CREATE TABLE IF NOT EXISTS `pedidos` (
  `id_pedido` int(11) NOT NULL AUTO_INCREMENT,
  `id_cliente` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  PRIMARY KEY (`id_pedido`),
  KEY `fk_pedidos_cliente` (`id_cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pedidos`
--

INSERT INTO `pedidos` (`id_pedido`, `id_cliente`, `fecha`) VALUES
(1, 4, '2026-09-10'),
(2, 4, '2026-09-10'),
(3, 4, '2026-09-10'),
(4, 4, '2026-09-10'),
(5, 4, '2026-09-10'),
(6, 4, '2026-09-10'),
(7, 4, '2026-09-10'),
(8, 4, '2026-09-10'),
(9, 4, '2026-09-10'),
(10, 4, '2026-09-10'),
(11, 4, '2026-09-10'),
(12, 4, '2026-09-10'),
(13, 4, '2026-09-10'),
(14, 4, '2026-09-10'),
(15, 4, '2026-09-10'),
(16, 4, '2026-09-10'),
(17, 4, '2026-09-10'),
(18, 4, '2026-09-10');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

DROP TABLE IF EXISTS `productos`;
CREATE TABLE IF NOT EXISTS `productos` (
  `id_producto` int(11) NOT NULL AUTO_INCREMENT,
  `id_categoria` int(11) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `stock` int(11) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_producto`),
  KEY `fk_productos_categoria` (`id_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id_producto`, `id_categoria`, `nombre`, `stock`, `precio`) VALUES
(1, 6, 'Jugo Verde Detox', 80, 4.50),
(2, 7, 'Barra de Proteína', 60, 2.50),
(3, 3, 'Vitamina C 1000mg', 100, 12.00),
(4, 9, 'Almendras Tostadas', 100, 5.00),
(5, 5, 'Whey Protein 1kg', 100, 45.00),
(6, 6, 'toalla facial hombre', 99, 8900.00),
(7, 6, 'serum facial hombre', 99, 95000.00),
(8, 6, 'protector solar hombre', 100, 69000.00),
(9, 6, 'limpiador facial hombre', 100, 26000.00),
(10, 6, 'crema hidratante hombre', 100, 19000.00),
(11, 7, 'balsamo para hombre', 100, 17000.00),
(12, 7, 'aceite de coco hombre', 100, 15000.00),
(13, 6, 'tonico facial', 100, 33500.00),
(14, 6, 'serum vitamina c', 100, 70000.00),
(15, 6, 'mascarillas y crema hidratante', 100, 45000.00),
(16, 6, 'gel purificante y protector solar', 100, 35000.00),
(17, 6, 'brochas y rodillo facial', 100, 30000.00),
(18, 6, 'banda para el pelo', 100, 25000.00),
(19, 6, 'agua micelar', 100, 20000.00),
(20, 7, 'aceite de coco mujer', 100, 15000.00),
(21, 6, 'serum facial mixto', 100, 45000.00),
(22, 6, 'protector solar mixto', 100, 17000.00),
(23, 7, 'aceite de coco mixto', 99, 15000.00),
(24, 6, 'crema hidratante mixto', 100, 15000.00),
(25, 6, 'limpiador facial mixto', 100, 20000.00),
(26, 7, 'balsamo mixto', 100, 8000.00),
(27, 6, 'agua micelar mixto', 100, 25000.00),
(28, 9, 'Aceite para perros', 100, 18000.00),
(29, 9, 'antiseptico para heridas de perro', 100, 18000.00),
(30, 9, 'Bolsas plásticas', 100, 32000.00),
(31, 9, 'gasas para perro', 100, 44000.00),
(32, 9, 'guantes desechables', 100, 26000.00),
(33, 9, 'Juguete para perro', 100, 8000.00),
(34, 9, 'libretapara informacion medica', 100, 5000.00),
(35, 9, 'medicinas para perros', 100, 14000.00),
(36, 9, 'pinzas y tijeras', 100, 14000.00),
(37, 9, 'Termómetro digital para perros', 100, 22000.00),
(38, 9, 'Vendas veterinarias', 100, 15000.00),
(39, 7, 'Aceite de coco', 100, 43.50),
(40, 10, 'Antisépticos', 99, 44.00),
(41, 7, 'Cremas', 100, 45.50),
(42, 10, 'Curitas', 100, 46.00),
(43, 10, 'Gasas estériles', 100, 47.50),
(44, 10, 'Gel antibacterial', 100, 48.00),
(45, 10, 'Medicina básica', 100, 49.50),
(46, 10, 'Termómetro digital', 100, 50.00),
(47, 10, 'Tijeras, pinzas y cinta', 100, 51.50),
(48, 7, 'Toalla', 100, 52.00),
(49, 10, 'Vendas elásticas', 100, 53.50);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `repartidores`
--

DROP TABLE IF EXISTS `repartidores`;
CREATE TABLE IF NOT EXISTS `repartidores` (
  `id_repartidor` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_repartidor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

DROP TABLE IF EXISTS `roles`;
CREATE TABLE IF NOT EXISTS `roles` (
  `id_rol` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  PRIMARY KEY (`id_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`id_rol`, `nombre`, `descripcion`) VALUES
(1, 'Administrador', 'Control total del sistema y gestión de usuarios'),
(2, 'Empleado', 'Gestiona productos, pedidos e inventario'),
(3, 'Cliente', 'Realiza compras en la tienda');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `id_rol` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `correo` (`correo`),
  KEY `fk_usuarios_rol` (`id_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id_usuario`, `nombre`, `correo`, `password`, `id_rol`) VALUES
(1, 'Admin General', 'admin@healthyfast.com', 'hector009', 1),
(2, 'Sofía Administradora', 'sofia.admin@healthyfast.com', 'hector010', 1),
(3, 'Carlos Empleado', 'empleado@healthyfast.com', 'roro2', 2),
(4, 'Marta Bodega', 'marta.empleada@healthyfast.com', 'roro3', 2),
(5, 'Jorge Caja', 'jorge.empleado@healthyfast.com', 'roro4', 2),
(6, 'Laura Cliente', 'cliente@healthyfast.com', 'roro6', 3),
(7, 'Pedro Comprador', 'pedro.cliente@healthyfast.com', 'roro7', 3),
(8, 'Ana Compradora', 'ana.cliente@healthyfast.com', 'roro8', 3);

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD CONSTRAINT `fk_clientes_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`);

--
-- Filtros para la tabla `despachos`
--
ALTER TABLE `despachos`
  ADD CONSTRAINT `fk_despachos_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`),
  ADD CONSTRAINT `fk_despachos_repartidor` FOREIGN KEY (`id_repartidor`) REFERENCES `repartidores` (`id_repartidor`);

--
-- Filtros para la tabla `detalle_movimiento`
--
ALTER TABLE `detalle_movimiento`
  ADD CONSTRAINT `fk_detmov_movimiento` FOREIGN KEY (`id_movimiento`) REFERENCES `movimientos_inventario` (`id_movimiento`),
  ADD CONSTRAINT `fk_detmov_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`);

--
-- Filtros para la tabla `detalle_pedido`
--
ALTER TABLE `detalle_pedido`
  ADD CONSTRAINT `fk_detped_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`),
  ADD CONSTRAINT `fk_detped_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`);

--
-- Filtros para la tabla `devoluciones`
--
ALTER TABLE `devoluciones`
  ADD CONSTRAINT `fk_devoluciones_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`);

--
-- Filtros para la tabla `empleados`
--
ALTER TABLE `empleados`
  ADD CONSTRAINT `fk_empleados_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`);

--
-- Filtros para la tabla `facturas`
--
ALTER TABLE `facturas`
  ADD CONSTRAINT `fk_facturas_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`);

--
-- Filtros para la tabla `pagos`
--
ALTER TABLE `pagos`
  ADD CONSTRAINT `fk_pagos_factura` FOREIGN KEY (`id_factura`) REFERENCES `facturas` (`id_factura`);

--
-- Filtros para la tabla `pedidos`
--
ALTER TABLE `pedidos`
  ADD CONSTRAINT `fk_pedidos_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`);

--
-- Filtros para la tabla `productos`
--
ALTER TABLE `productos`
  ADD CONSTRAINT `fk_productos_categoria` FOREIGN KEY (`id_categoria`) REFERENCES `categorias` (`id_categoria`);

--
-- Filtros para la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
